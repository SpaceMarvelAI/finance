# Data Layer

The Data Layer provides persistent storage and data management capabilities for the Financial Automation System. It handles all database operations, document storage, and data retrieval.

## 📊 Overview

The Data Layer is responsible for:
- **Document Storage**: Persistent storage of all uploaded financial documents
- **Database Management**: PostgreSQL connection management and ORM models
- **Data Access**: CRUD operations and data retrieval patterns
- **Schema Management**: Database schema definition and migrations

## 🏗️ Architecture

```
data_layer/
├── database/           # Database connection and management
│   ├── database_manager.py     # Main database interface
│   ├── database_models.py      # SQLAlchemy ORM models
│   ├── document_repository.py  # Document-specific operations
│   ├── init_db.py             # Database initialization
│   └── schema.sql             # Database schema definition
├── models/             # Data models and schemas
│   ├── database_models.py      # Core database models
│   └── enhanced_database_schema.py  # Extended schema definitions
├── repositories/       # Data access layer
│   └── document_repository.py  # Document repository
└── schemas/          # Data validation schemas
    └── canonical_schema.py     # Canonical data schema
```

## 🔧 Key Components

### Database Manager (`database_manager.py`)

**Purpose**: Central database management interface that handles PostgreSQL connections and operations.

**Key Features**:
- Connection pooling for optimal performance
- Document CRUD operations
- Statistics and reporting queries
- Date parsing and currency conversion
- RealDictCursor support for dictionary results

**Usage**:
```python
from data_layer.database.database_manager import get_database

# Get database instance
db = get_database()

# Insert a document
doc_id = db.insert_document({
    'company_id': 'company-123',
    'file_name': 'invoice.pdf',
    'grand_total': 1000.0,
    'category': 'purchase'
})

# Get documents by category
documents = db.get_documents_by_category('purchase', 'company-123')
```

**Methods**:
- `insert_document(document_data)` - Insert new document
- `get_all_documents(company_id)` - Get all documents for company
- `get_documents_by_category(category, company_id)` - Filter by category
- `get_document_by_id(doc_id)` - Get specific document
- `delete_document(doc_id)` - Delete document
- `get_statistics(company_id)` - Get database statistics

### Database Models (`database_models.py`)

**Purpose**: SQLAlchemy ORM models that define the database schema structure.

**Key Models**:
- **User**: User authentication and management
- **Company**: Company settings and branding
- **Document**: Financial document storage
- **Workflow**: Workflow execution history

**Schema Details**:
```python
class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True)
    company_id = Column(String(36), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500))
    file_type = Column(String(10))
    document_type = Column(String(50))
    document_number = Column(String(100))
    document_date = Column(DateTime)
    category = Column(String(50))  # purchase, sales, etc.
    grand_total = Column(Numeric(15, 2))
    tax_total = Column(Numeric(15, 2))
    outstanding = Column(Numeric(15, 2))
    vendor_name = Column(String(255))
    customer_name = Column(String(255))
    docling_parsed_data = Column(JSONB)  # AI-parsed data
    canonical_data = Column(JSONB)      # Standardized data
    status = Column(String(50))         # pending, processed, failed
    uploaded_at = Column(DateTime)
    processed_at = Column(DateTime)
```

### Document Repository (`document_repository.py`)

**Purpose**: Specialized data access layer for document operations.

**Key Features**:
- Advanced document querying
- Bulk operations support
- Document status management
- Integration with processing layer

**Usage**:
```python
from data_layer.repositories.document_repository import DocumentRepository

repo = DocumentRepository()
documents = repo.find_by_status('processed', company_id='company-123')
```

### Enhanced Database Schema (`enhanced_database_schema.py`)

**Purpose**: Extended database schema with additional tables and relationships.

**Additional Tables**:
- **User Settings**: User preferences and configurations
- **Master Data**: Vendor and customer master records
- **Audit Logs**: Complete audit trail
- **Exchange Rates**: Currency conversion rates

## 📋 Database Schema

### Core Tables

#### Documents Table
Stores all uploaded financial documents with parsed data.

**Fields**:
- `id`: Unique document identifier (UUID)
- `company_id`: Company owning the document
- `file_name`: Original filename
- `file_path`: Storage path
- `category`: Document category (purchase, sales, etc.)
- `grand_total`: Total amount in INR
- `tax_total`: Tax amount
- `outstanding`: Outstanding balance
- `vendor_name`: Vendor information
- `customer_name`: Customer information
- `docling_parsed_data`: AI-parsed structured data
- `canonical_data`: Standardized data format
- `status`: Processing status
- `uploaded_at`: Upload timestamp
- `processed_at`: Processing completion timestamp

#### Users Table
User authentication and management.

**Fields**:
- `id`: User identifier
- `email`: User email (unique)
- `password_hash`: BCrypt hashed password
- `full_name`: User's full name
- `company_id`: Associated company
- `is_active`: Account status
- `created_at`: Account creation timestamp
- `last_login`: Last login timestamp

#### Companies Table
Company settings and branding information.

**Fields**:
- `id`: Company identifier
- `name`: Company name
- `primary_color`: Branding color
- `secondary_color`: Secondary branding color
- `currency`: Default currency
- `logo_url`: Company logo URL
- `company_aliases`: Alternative company names
- `is_active`: Company status

## 🔌 Integration Points

### With Processing Layer
```python
# Document processing service uses database manager
from data_layer.database.database_manager import get_database

class DocumentProcessingService:
    def __init__(self, db_session, company_id):
        self.db = db_session  # DatabaseManager instance
        self.company_id = company_id
    
    def process_document(self, file_path, file_name):
        # Process document and save to database
        result = self.db.insert_document({
            'company_id': self.company_id,
            'file_name': file_name,
            'file_path': file_path,
            # ... other fields
        })
        return result
```

### With Intelligence Layer
```python
# Workflow execution stores results in database
from data_layer.database.database_manager import get_database

class WorkflowExecutor:
    def execute_workflow(self, workflow_definition):
        # Execute workflow
        result = self.run_workflow(workflow_definition)
        
        # Store execution result
        db = get_database()
        db.store_workflow_result({
            'workflow_id': workflow_definition['id'],
            'execution_result': result,
            'status': 'completed'
        })
```

## 🚀 Performance Considerations

### Connection Pooling
- Uses PostgreSQL connection pooling for optimal performance
- Configurable pool size based on workload
- Automatic connection management

### Indexing Strategy
- Indexes on frequently queried fields:
  - `company_id` for multi-tenancy
  - `category` for document filtering
  - `document_date` for date-based queries
  - `status` for processing state queries

### Query Optimization
- Uses RealDictCursor for dictionary results
- Prepared statements for security
- Bulk operations for batch processing

## 🔧 Configuration

### Environment Variables
```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=financial_automation
DB_USER=postgres
DB_PASSWORD=postgres
```

### Database Initialization
```python
from data_layer.database.init_db import initialize_database

# Initialize database schema
initialize_database()
```

## 🧪 Testing

### Unit Tests
```python
import pytest
from data_layer.database.database_manager import DatabaseManager

def test_insert_document():
    db = DatabaseManager()
    doc_id = db.insert_document({
        'company_id': 'test-company',
        'file_name': 'test.pdf',
        'grand_total': 100.0
    })
    assert doc_id is not None
```

### Integration Tests
```python
def test_document_lifecycle():
    # Test complete document lifecycle
    db = get_database()
    
    # Insert document
    doc_id = db.insert_document(test_data)
    
    # Retrieve document
    doc = db.get_document_by_id(doc_id)
    assert doc['id'] == doc_id
    
    # Update document
    # ...
    
    # Delete document
    result = db.delete_document(doc_id)
    assert result is True
```

## 📈 Monitoring and Maintenance

### Database Statistics
```python
# Get database statistics
db = get_database()
stats = db.get_statistics(company_id='company-123')

print(f"Total documents: {stats['total_documents']}")
print(f"Purchase invoices: {stats['purchase_invoices']}")
print(f"Total payables: ₹{stats['total_payables']}")
```

### Health Checks
```python
def check_database_health():
    try:
        db = get_database()
        stats = db.get_statistics()
        return {
            'status': 'healthy',
            'total_documents': stats['total_documents'],
            'last_updated': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }
```

## 🔒 Security

### Data Encryption
- Passwords hashed with BCrypt
- Sensitive data encryption at rest
- Secure connection strings

### Access Control
- Company-level data isolation
- Role-based access control
- Audit logging for all operations

### Best Practices
- Parameterized queries to prevent SQL injection
- Connection string security
- Regular security audits

---

**Next Layer**: [Intelligence Layer](../intelligence_layer/README.md) - AI orchestration and routing