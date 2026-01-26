"""
COMPLETE DATABASE INITIALIZATION SCRIPT
Sets up entire financial automation database from scratch

Creates:
1. Core master data tables (companies, vendors, customers)
2. Transaction tables (vendor_invoices, customer_invoices)
3. Document tables (documents)
4. Workflow persistence tables (workflows, workflow_execution_logs)
5. Sample data for testing

Run this on an empty database to get started.
"""

from sqlalchemy import create_engine, text
import os
import sys


# SQL Schema for complete database setup
COMPLETE_SCHEMA = """
-- ============================================================================
-- MASTER DATA TABLES
-- ============================================================================

-- Companies (tenants)
CREATE TABLE IF NOT EXISTS companies (
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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vendors (suppliers - AP)
CREATE TABLE IF NOT EXISTS vendors (
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
    credit_limit DECIMAL(15,2),
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- Customers (buyers - AR)
CREATE TABLE IF NOT EXISTS customers (
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
    credit_limit DECIMAL(15,2),
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- ============================================================================
-- DOCUMENT STORAGE
-- ============================================================================

CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(36) PRIMARY KEY,
    company_id VARCHAR(36) NOT NULL,
    
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    file_type VARCHAR(10),
    file_size INTEGER,
    
    document_type VARCHAR(50),
    document_number VARCHAR(100),
    document_date TIMESTAMP,
    category VARCHAR(50),
    
    docling_parsed_data JSONB,
    canonical_data JSONB,
    
    status VARCHAR(50) DEFAULT 'pending',
    confidence_score DECIMAL(3,2),
    
    vendor_name VARCHAR(255),
    customer_name VARCHAR(255),
    grand_total DECIMAL(15,2) DEFAULT 0.0,
    tax_total DECIMAL(15,2) DEFAULT 0.0,
    paid_amount DECIMAL(15,2) DEFAULT 0.0,
    outstanding DECIMAL(15,2) DEFAULT 0.0,
    
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parsed_at TIMESTAMP,
    processed_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- ============================================================================
-- TRANSACTION TABLES
-- ============================================================================

-- Vendor Invoices (AP - Accounts Payable)
CREATE TABLE IF NOT EXISTS vendor_invoices (
    id VARCHAR(36) PRIMARY KEY,
    company_id VARCHAR(36) NOT NULL,
    vendor_id VARCHAR(36),
    document_id VARCHAR(36),
    
    invoice_number VARCHAR(100) NOT NULL,
    invoice_date TIMESTAMP,
    due_date TIMESTAMP,
    
    subtotal_amount DECIMAL(15,2),
    tax_amount DECIMAL(15,2),
    total_amount DECIMAL(15,2),
    paid_amount DECIMAL(15,2) DEFAULT 0.0,
    outstanding_amount DECIMAL(15,2),
    
    original_currency VARCHAR(3),
    exchange_rate DECIMAL(10,6),
    inr_amount DECIMAL(15,2),
    
    payment_status VARCHAR(20) DEFAULT 'unpaid',
    payment_terms_days INTEGER,
    
    line_items JSONB,
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (company_id) REFERENCES companies(id),
    FOREIGN KEY (vendor_id) REFERENCES vendors(id),
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- Customer Invoices (AR - Accounts Receivable)
CREATE TABLE IF NOT EXISTS customer_invoices (
    id VARCHAR(36) PRIMARY KEY,
    company_id VARCHAR(36) NOT NULL,
    customer_id VARCHAR(36),
    document_id VARCHAR(36),
    
    invoice_number VARCHAR(100) NOT NULL,
    invoice_date TIMESTAMP,
    due_date TIMESTAMP,
    
    subtotal_amount DECIMAL(15,2),
    tax_amount DECIMAL(15,2),
    total_amount DECIMAL(15,2),
    received_amount DECIMAL(15,2) DEFAULT 0.0,
    outstanding_amount DECIMAL(15,2),
    
    original_currency VARCHAR(3),
    exchange_rate DECIMAL(10,6),
    inr_amount DECIMAL(15,2),
    
    payment_status VARCHAR(20) DEFAULT 'unpaid',
    payment_terms_days INTEGER,
    
    line_items JSONB,
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (company_id) REFERENCES companies(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- ============================================================================
-- WORKFLOW PERSISTENCE TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS workflows (
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

CREATE TABLE IF NOT EXISTS workflow_execution_logs (
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
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Companies
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);

-- Vendors
CREATE INDEX IF NOT EXISTS idx_vendors_company ON vendors(company_id);
CREATE INDEX IF NOT EXISTS idx_vendors_name ON vendors(vendor_name);
CREATE INDEX IF NOT EXISTS idx_vendors_active ON vendors(is_active);

-- Customers
CREATE INDEX IF NOT EXISTS idx_customers_company ON customers(company_id);
CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(customer_name);
CREATE INDEX IF NOT EXISTS idx_customers_active ON customers(is_active);

-- Documents
CREATE INDEX IF NOT EXISTS idx_documents_company ON documents(company_id);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
CREATE INDEX IF NOT EXISTS idx_documents_number ON documents(document_number);
CREATE INDEX IF NOT EXISTS idx_documents_uploaded ON documents(uploaded_at);

-- Vendor Invoices
CREATE INDEX IF NOT EXISTS idx_vendor_invoices_company ON vendor_invoices(company_id);
CREATE INDEX IF NOT EXISTS idx_vendor_invoices_vendor ON vendor_invoices(vendor_id);
CREATE INDEX IF NOT EXISTS idx_vendor_invoices_status ON vendor_invoices(payment_status);
CREATE INDEX IF NOT EXISTS idx_vendor_invoices_date ON vendor_invoices(invoice_date);
CREATE INDEX IF NOT EXISTS idx_vendor_invoices_due ON vendor_invoices(due_date);

-- Customer Invoices
CREATE INDEX IF NOT EXISTS idx_customer_invoices_company ON customer_invoices(company_id);
CREATE INDEX IF NOT EXISTS idx_customer_invoices_customer ON customer_invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_invoices_status ON customer_invoices(payment_status);
CREATE INDEX IF NOT EXISTS idx_customer_invoices_date ON customer_invoices(invoice_date);
CREATE INDEX IF NOT EXISTS idx_customer_invoices_due ON customer_invoices(due_date);

-- Workflows
CREATE INDEX IF NOT EXISTS idx_workflows_company ON workflows(company_id);
CREATE INDEX IF NOT EXISTS idx_workflows_user ON workflows(user_id);
CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);
CREATE INDEX IF NOT EXISTS idx_workflows_created ON workflows(created_at);

-- Workflow Logs
CREATE INDEX IF NOT EXISTS idx_workflow_logs_workflow ON workflow_execution_logs(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_logs_created ON workflow_execution_logs(created_at);
"""


# Sample data for testing
SAMPLE_DATA = """
-- ============================================================================
-- SAMPLE DATA FOR TESTING
-- ============================================================================

-- Sample Company
INSERT INTO companies (id, name, tax_id, email, phone, currency, is_active)
VALUES 
    ('company-001', 'Acme Corporation', 'TAX001', 'info@acme.com', '+91-9876543210', 'INR', TRUE),
    ('company-002', 'Tech Solutions Ltd', 'TAX002', 'contact@techsol.com', '+91-9876543211', 'USD', TRUE)
ON CONFLICT (id) DO NOTHING;

-- Sample Vendors
INSERT INTO vendors (id, company_id, vendor_name, vendor_code, email, phone, payment_terms_days, is_active)
VALUES 
    ('vendor-001', 'company-001', 'Office Supplies Inc', 'V001', 'sales@officesupplies.com', '+91-1234567890', 30, TRUE),
    ('vendor-002', 'company-001', 'Tech Equipment Co', 'V002', 'support@techequip.com', '+91-1234567891', 45, TRUE),
    ('vendor-003', 'company-001', 'Consulting Services Ltd', 'V003', 'info@consulting.com', '+91-1234567892', 15, TRUE)
ON CONFLICT (id) DO NOTHING;

-- Sample Customers
INSERT INTO customers (id, company_id, customer_name, customer_code, email, phone, payment_terms_days, credit_limit, is_active)
VALUES 
    ('customer-001', 'company-001', 'Global Retail Corp', 'C001', 'ap@globalretail.com', '+91-9876543200', 30, 1000000.00, TRUE),
    ('customer-002', 'company-001', 'Enterprise Solutions Inc', 'C002', 'billing@enterprise.com', '+91-9876543201', 45, 2000000.00, TRUE),
    ('customer-003', 'company-001', 'Startup Innovations', 'C003', 'finance@startup.com', '+91-9876543202', 15, 500000.00, TRUE)
ON CONFLICT (id) DO NOTHING;

-- Sample Vendor Invoices (AP)
INSERT INTO vendor_invoices (
    id, company_id, vendor_id, invoice_number, invoice_date, due_date,
    subtotal_amount, tax_amount, total_amount, outstanding_amount,
    original_currency, inr_amount, payment_status, payment_terms_days
)
VALUES 
    (
        'vinv-001', 'company-001', 'vendor-001', 'INV-2025-001', 
        '2025-01-01'::TIMESTAMP, '2025-01-31'::TIMESTAMP,
        10000.00, 1800.00, 11800.00, 11800.00,
        'INR', 11800.00, 'unpaid', 30
    ),
    (
        'vinv-002', 'company-001', 'vendor-002', 'INV-2025-002',
        '2025-01-05'::TIMESTAMP, '2025-02-04'::TIMESTAMP,
        50000.00, 9000.00, 59000.00, 59000.00,
        'INR', 59000.00, 'unpaid', 30
    ),
    (
        'vinv-003', 'company-001', 'vendor-003', 'INV-2024-050',
        '2024-12-15'::TIMESTAMP, '2024-12-30'::TIMESTAMP,
        25000.00, 4500.00, 29500.00, 29500.00,
        'INR', 29500.00, 'overdue', 15
    )
ON CONFLICT (id) DO NOTHING;

-- Sample Customer Invoices (AR)
INSERT INTO customer_invoices (
    id, company_id, customer_id, invoice_number, invoice_date, due_date,
    subtotal_amount, tax_amount, total_amount, outstanding_amount,
    original_currency, inr_amount, payment_status, payment_terms_days
)
VALUES 
    (
        'cinv-001', 'company-001', 'customer-001', 'SI-2025-001',
        '2025-01-10'::TIMESTAMP, '2025-02-09'::TIMESTAMP,
        100000.00, 18000.00, 118000.00, 118000.00,
        'INR', 118000.00, 'unpaid', 30
    ),
    (
        'cinv-002', 'company-001', 'customer-002', 'SI-2025-002',
        '2025-01-15'::TIMESTAMP, '2025-03-01'::TIMESTAMP,
        250000.00, 45000.00, 295000.00, 147500.00,
        'INR', 295000.00, 'partial', 45
    ),
    (
        'cinv-003', 'company-001', 'customer-003', 'SI-2024-100',
        '2024-12-20'::TIMESTAMP, '2025-01-04'::TIMESTAMP,
        75000.00, 13500.00, 88500.00, 88500.00,
        'INR', 88500.00, 'overdue', 15
    )
ON CONFLICT (id) DO NOTHING;

-- Sample Documents
INSERT INTO documents (
    id, company_id, file_name, file_type, document_type, document_number,
    category, vendor_name, grand_total, status, uploaded_at
)
VALUES 
    (
        'doc-001', 'company-001', 'invoice_001.pdf', 'pdf', 'vendor_invoice', 'INV-2025-001',
        'purchase', 'Office Supplies Inc', 11800.00, 'completed', '2025-01-01'::TIMESTAMP
    ),
    (
        'doc-002', 'company-001', 'invoice_002.pdf', 'pdf', 'customer_invoice', 'SI-2025-001',
        'sales', 'Global Retail Corp', 118000.00, 'completed', '2025-01-10'::TIMESTAMP
    )
ON CONFLICT (id) DO NOTHING;
"""


def run_initialization(database_url: str):
    """
    Initialize complete database schema
    
    Args:
        database_url: PostgreSQL connection string
    """
    print("=" * 80)
    print("DATABASE INITIALIZATION - Complete Schema Setup")
    print("=" * 80)
    print()
    
    db_display = database_url.split('@')[1] if '@' in database_url else database_url
    print(f"Database: {db_display}")
    print()
    
    try:
        # Create engine
        engine = create_engine(database_url, echo=False)
        
        # Execute schema creation
        print("Creating tables...")
        print()
        
        with engine.connect() as conn:
            # Execute main schema
            for statement in COMPLETE_SCHEMA.split(';'):
                statement = statement.strip()
                if statement:
                    try:
                        conn.execute(text(statement))
                        conn.commit()
                    except Exception as e:
                        print(f"Warning: {e}")
                        continue
            
            print(" Tables created successfully")
            print()
            
            # Insert sample data
            print("Inserting sample data...")
            print()
            
            for statement in SAMPLE_DATA.split(';'):
                statement = statement.strip()
                if statement:
                    try:
                        conn.execute(text(statement))
                        conn.commit()
                    except Exception as e:
                        print(f"Warning: {e}")
                        continue
            
            print(" Sample data inserted")
            print()
        
        # Verify tables
        print("Verifying setup...")
        print()
        
        with engine.connect() as conn:
            # Count tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            
            print(f"Tables created: {len(tables)}")
            for table in tables:
                print(f"   {table}")
            
            print()
            
            # Count sample data
            print("Sample data counts:")
            
            counts = {
                'companies': conn.execute(text("SELECT COUNT(*) FROM companies")).scalar(),
                'vendors': conn.execute(text("SELECT COUNT(*) FROM vendors")).scalar(),
                'customers': conn.execute(text("SELECT COUNT(*) FROM customers")).scalar(),
                'vendor_invoices': conn.execute(text("SELECT COUNT(*) FROM vendor_invoices")).scalar(),
                'customer_invoices': conn.execute(text("SELECT COUNT(*) FROM customer_invoices")).scalar(),
                'documents': conn.execute(text("SELECT COUNT(*) FROM documents")).scalar(),
            }
            
            for table, count in counts.items():
                print(f"  {table}: {count} records")
        
        print()
        print("=" * 80)
        print(" DATABASE INITIALIZATION COMPLETE!")
        print("=" * 80)
        print()
        print("Next steps:")
        print("  1. Start the API: python production_api.py")
        print("  2. Check health: curl http://localhost:8000/health")
        print("  3. Upload a document to test")
        print()
        
        return True
        
    except Exception as e:
        print()
        print(f" Initialization failed: {e}")
        print()
        import traceback
        traceback.print_exc()
        print()
        print("=" * 80)
        return False


if __name__ == "__main__":
    # Get database URL from environment or use default
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/financial_automation"
    )
    
    # Allow override via command line
    if len(sys.argv) > 1:
        database_url = sys.argv[1]
    
    print()
    print("This script will:")
    print("  1. Create all necessary tables")
    print("  2. Create indexes for performance")
    print("  3. Insert sample data for testing")
    print()
    print(f"Database URL: {database_url}")
    print()
    
    response = input("Continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        success = run_initialization(database_url)
        sys.exit(0 if success else 1)
    else:
        print("Initialization cancelled.")
        sys.exit(0)