# Processing Layer

The Processing Layer is the core execution engine of the Financial Automation System. It handles document processing, agent execution, workflow management, and report generation. This layer transforms raw documents into structured data and executes complex financial operations.

## ⚙️ Overview

The Processing Layer is responsible for:
- **Document Processing**: AI-powered parsing and extraction from various document formats
- **Agent Execution**: Running specialized financial agents for different domains
- **Workflow Management**: Executing configurable multi-step workflows
- **Report Generation**: Creating branded Excel reports with professional formatting
- **Data Transformation**: Converting raw data into canonical formats

## 🏗️ Architecture

```
processing_layer/
├── document_processing/    # Document ingestion and parsing
│   ├── document_processing_service.py  # Main processing service
│   ├── document_processor.py           # Document processor
│   ├── enhanced_ingestion_agent.py     # Enhanced document ingestion
│   ├── parsers/                        # Document parsers
│   │   ├── universal_docling_parser.py # AI document parser
│   │   ├── csv_parser.py              # CSV parser
│   │   └── parsed_data_validator.py   # Data validation
│   └── services/                       # Processing services
├── agents/              # Specialized financial agents
│   ├── accounts_payable/               # AP-specific agents
│   │   ├── ap_aging_agent.py          # AP aging analysis
│   │   ├── ap_register_agent.py       # AP register generation
│   │   ├── ap_overdue_agent.py        # AP overdue analysis
│   │   └── ap_duplicate_agent.py      # Duplicate detection
│   ├── accounts_receivable/            # AR-specific agents
│   │   ├── ar_aging_agent.py          # AR aging analysis
│   │   ├── ar_register_agent.py       # AR register generation
│   │   └── ar_collection_agent.py     # Collection analysis
│   ├── core/                           # Base agent classes
│   │   ├── base_agent.py              # Base agent implementation
│   │   ├── configurable_workflow_agent.py  # Configurable workflows
│   │   └── rule_based_agent.py        # Rule-based processing
│   ├── monitoring_analysis/            # Monitoring and analysis
│   └── reconciliation/                 # Reconciliation agents
├── workflows/           # Workflow execution engine
│   ├── execution/                      # Workflow execution
│   │   ├── workflow_executor.py       # Main executor
│   │   └── workflow_runner.py         # Workflow runner
│   └── nodes/                          # Processing nodes
│       ├── base_node.py               # Base node class
│       ├── data_nodes.py              # Data fetching nodes
│       ├── calculation_nodes.py       # Calculation nodes
│       ├── aggregation_nodes.py       # Aggregation nodes
│       ├── output_nodes.py            # Output generation nodes
│       └── node_registry.py           # Node registration
└── report_generation/   # Report creation and formatting
    ├── ap_aging_report.py             # AP aging reports
    ├── ap_invoice_register.py         # AP invoice register
    ├── ar_aging_report.py             # AR aging reports
    ├── branded_excel_generator.py     # Branded Excel reports
    ├── excel_generator.py             # Excel generation
    └── report_generator.py            # Base report generator
```

## 📄 Document Processing

### Document Processing Service (`document_processing_service.py`)

**Purpose**: Main service for processing uploaded documents through the complete pipeline.

**Key Features**:
- **Multi-format Support**: PDF, CSV, DOCX, images
- **AI-Powered Parsing**: Uses Docling for intelligent document understanding
- **Data Validation**: Validates extracted data for accuracy
- **Canonical Transformation**: Converts data to standardized format
- **Error Handling**: Comprehensive error handling and retry logic

**Usage**:
```python
from processing_layer.document_processing.document_processing_service import DocumentProcessingService

# Initialize service
processor = DocumentProcessingService(
    db_session=db_manager,
    docling_parser=docling_parser,
    company_id='company-123',
    user_company_name='Your Company'
)

# Process uploaded document
result = processor.process_upload(
    file_path='/path/to/invoice.pdf',
    file_name='invoice.pdf'
)

print(f"Document ID: {result['document_id']}")
print(f"Category: {result['invoice_category']}")
print(f"Extracted Data: {result['extracted_data']}")
```

**Processing Pipeline**:
1. **File Validation**: Check file format and size
2. **Document Parsing**: Extract text and structured data
3. **Data Validation**: Validate extracted information
4. **Canonical Transformation**: Convert to standard format
5. **Database Storage**: Save to PostgreSQL
6. **Result Return**: Return processing results

### Universal Docling Parser (`universal_docling_parser.py`)

**Purpose**: AI-powered document parser using Docling for intelligent document understanding.

**Key Features**:
- **Multi-format Support**: PDF, DOCX, images, scanned documents
- **AI Extraction**: Uses machine learning for accurate data extraction
- **Layout Understanding**: Understands document structure and layout
- **Confidence Scoring**: Provides confidence scores for extracted data
- **Error Recovery**: Handles parsing errors gracefully

**Usage**:
```python
from processing_layer.document_processing.parsers.universal_docling_parser import UniversalDoclingParser

parser = UniversalDoclingParser()

# Parse document
result = parser.parse('/path/to/document.pdf')

print(f"Extracted Text: {result['text']}")
print(f"Tables: {len(result['tables'])}")
print(f"Figures: {len(result['figures'])}")
```

### CSV Parser (`csv_parser.py`)

**Purpose**: Specialized parser for CSV files with financial data.

**Key Features**:
- **Header Detection**: Automatically detects column headers
- **Data Type Inference**: Infers data types from content
- **Currency Handling**: Handles different currency formats
- **Date Parsing**: Parses various date formats
- **Validation**: Validates CSV structure and content

**Usage**:
```python
from processing_layer.document_processing.parsers.csv_parser import CSVParser

parser = CSVParser()

# Parse CSV
result = parser.parse('/path/to/invoice.csv')

print(f"Headers: {result['headers']}")
print(f"Rows: {len(result['rows'])}")
print(f"Data: {result['data']}")
```

## 🤖 Financial Agents

### AP Aging Agent (`agents/accounts_payable/ap_aging_agent.py`)

**Purpose**: Generates AP aging analysis reports showing outstanding payables by time buckets.

**Key Features**:
- **Aging Buckets**: 0-30, 31-60, 61-90, 90+ days
- **Vendor Analysis**: Groups by vendor for vendor-specific aging
- **Currency Support**: Multi-currency aging with live exchange rates
- **Trend Analysis**: Shows aging trends over time
- **Export Options**: Excel, CSV, PDF export

**Usage**:
```python
from processing_layer.agents.accounts_payable.ap_aging_agent import APAgingAgent

agent = APAgingAgent()

# Generate AP aging report
result = agent.execute(
    params={
        'user_id': 'user-123',
        'company_id': 'company-456',
        'as_of_date': '2024-12-31',
        'include_paid': False,
        'min_aging_days': 0
    }
)

print(f"Report Status: {result['status']}")
print(f"File Path: {result['file_path']}")
print(f"Total Invoices: {result['data']['total_invoices']}")
```

**Report Output**:
- **Summary**: Total outstanding, average aging, vendor count
- **Aging Buckets**: Breakdown by time periods
- **Vendor Details**: Individual vendor aging analysis
- **Trends**: Historical aging comparison

### AP Register Agent (`agents/accounts_payable/ap_register_agent.py`)

**Purpose**: Generates complete AP invoice register with all vendor transactions.

**Key Features**:
- **Complete Register**: All invoices with full details
- **Vendor Information**: Vendor contact and payment details
- **Status Tracking**: Invoice status (pending, paid, partial)
- **Search and Filter**: Advanced filtering capabilities
- **Export Options**: Multiple export formats

**Usage**:
```python
from processing_layer.agents.accounts_payable.ap_register_agent import APRegisterAgent

agent = APRegisterAgent()

# Generate AP register
result = agent.execute(
    params={
        'user_id': 'user-123',
        'company_id': 'company-456',
        'date_from': '2024-01-01',
        'date_to': '2024-12-31',
        'vendor_filter': ['vendor-1', 'vendor-2']
    }
)

print(f"Register Status: {result['status']}")
print(f"Total Records: {result['data']['total_records']}")
```

### AR Aging Agent (`agents/accounts_receivable/ar_aging_agent.py`)

**Purpose**: Generates AR aging analysis for customer receivables.

**Key Features**:
- **Customer Aging**: Outstanding receivables by customer
- **DSO Calculation**: Days Sales Outstanding analysis
- **Credit Analysis**: Customer credit utilization
- **Collection Priorities**: Prioritizes collection efforts
- **Trend Analysis**: Historical receivables trends

**Usage**:
```python
from processing_layer.agents.accounts_receivable.ar_aging_agent import ARAgingAgent

agent = ARAgingAgent()

# Generate AR aging report
result = agent.execute(
    params={
        'user_id': 'user-123',
        'company_id': 'company-456',
        'as_of_date': '2024-12-31',
        'include_paid': False
    }
)

print(f"AR Aging Status: {result['status']}")
print(f"Total Receivables: ₹{result['data']['summary']['total_receivables']}")
```

## 🔄 Workflow Management

### Workflow Nodes (`workflows/nodes/`)

**Purpose**: Modular processing nodes that can be combined to create complex workflows.

**Node Types**:

#### Data Nodes (`data_nodes.py`)
- **InvoiceFetchNode**: Fetches invoices from database
- **PaymentFetchNode**: Fetches payment records
- **MasterDataNode**: Fetches vendor/customer master data
- **ConfigNode**: Fetches system configuration

#### Calculation Nodes (`calculation_nodes.py`)
- **OutstandingCalculatorNode**: Calculates outstanding amounts
- **AgingCalculatorNode**: Calculates aging buckets
- **CurrencyConverterNode**: Converts currencies
- **TaxCalculatorNode**: Calculates taxes

#### Aggregation Nodes (`aggregation_nodes.py`)
- **GroupingNode**: Groups data by specified criteria
- **SummaryNode**: Generates summary statistics
- **FilterNode**: Filters data based on conditions

#### Output Nodes (`output_nodes.py`)
- **ExcelGeneratorNode**: Generates Excel reports
- **PDFGeneratorNode**: Generates PDF reports
- **EmailNode**: Sends email notifications

**Usage**:
```python
from processing_layer.workflows.nodes import InvoiceFetchNode, OutstandingCalculatorNode, ExcelGeneratorNode

# Create workflow nodes
fetch_node = InvoiceFetchNode()
calc_node = OutstandingCalculatorNode()
excel_node = ExcelGeneratorNode()

# Execute workflow
invoices = fetch_node.run(params={'category': 'purchase', 'company_id': 'company-123'})
outstanding_invoices = calc_node.run(invoices)
report_path = excel_node.run(outstanding_invoices, params={'user_id': 'user-123'})
```

### Node Registry (`workflows/nodes/node_registry.py`)

**Purpose**: Central registry for all available workflow nodes.

**Features**:
- **Dynamic Registration**: Register nodes at runtime
- **Node Discovery**: Discover available nodes by category
- **Metadata Management**: Store node metadata and descriptions
- **Validation**: Validate node configurations

**Usage**:
```python
from processing_layer.workflows.nodes.node_registry import NodeRegistry

# Get all available nodes
all_nodes = NodeRegistry.get_all_nodes()
print(f"Available Nodes: {len(all_nodes)}")

# Get nodes by category
data_nodes = NodeRegistry.get_nodes_by_category('data')
calculation_nodes = NodeRegistry.get_nodes_by_category('calculation')
```

## 📊 Report Generation

### Branded Excel Generator (`branded_excel_generator.py`)

**Purpose**: Creates professional Excel reports with company branding and formatting.

**Key Features**:
- **Company Branding**: Logo, colors, and company information
- **Professional Formatting**: Headers, footers, and styling
- **Multiple Sheets**: Organized data across multiple worksheets
- **Charts and Graphs**: Visual data representation
- **Export Options**: Excel, CSV, PDF formats

**Usage**:
```python
from processing_layer.report_generation.branded_excel_generator import BrandedExcelGenerator

generator = BrandedExcelGenerator()

# Generate branded report
report_path = generator.generate_report(
    report_data={
        'summary': {'total': 100000, 'count': 50},
        'details': [{'invoice': 'INV-001', 'amount': 10000}, ...]
    },
    company_info={
        'name': 'Your Company',
        'logo_url': '/path/to/logo.png',
        'primary_color': '#1976D2'
    },
    report_title='AP Aging Report'
)

print(f"Report Generated: {report_path}")
```

**Report Features**:
- **Cover Page**: Company information and report details
- **Summary Sheet**: Key metrics and summary statistics
- **Detail Sheets**: Detailed transaction data
- **Charts**: Visual representations of data
- **Footer**: Page numbers and generation timestamp

### Report Generator (`report_generator.py`)

**Purpose**: Base class for all report generation with common functionality.

**Key Features**:
- **Template System**: Reusable report templates
- **Data Processing**: Common data processing logic
- **Export Management**: Unified export functionality
- **Error Handling**: Consistent error handling
- **Logging**: Comprehensive logging for debugging

**Usage**:
```python
from processing_layer.report_generation.report_generator import ReportGenerator

class CustomReportGenerator(ReportGenerator):
    def generate_report_data(self, params):
        # Custom data generation logic
        return processed_data
    
    def format_report(self, data):
        # Custom formatting logic
        return formatted_data

# Use custom generator
generator = CustomReportGenerator()
result = generator.generate(params={'report_type': 'custom'})
```

## 🧪 Testing

### Unit Tests
```python
import pytest
from processing_layer.agents.accounts_payable.ap_aging_agent import APAgingAgent

def test_ap_aging_agent():
    agent = APAgingAgent()
    
    result = agent.execute(
        params={
            'user_id': 'test-user',
            'company_id': 'test-company',
            'as_of_date': '2024-12-31'
        }
    )
    
    assert result['status'] == 'success'
    assert 'file_path' in result
    assert 'data' in result
```

### Integration Tests
```python
def test_document_processing_pipeline():
    # Test complete document processing pipeline
    processor = DocumentProcessingService(
        db_session=test_db,
        docling_parser=test_parser,
        company_id='test-company'
    )
    
    result = processor.process_upload(
        file_path='test_invoice.pdf',
        file_name='test_invoice.pdf'
    )
    
    assert result['success'] is True
    assert 'document_id' in result
    assert 'extracted_data' in result
```

## 🚀 Performance Optimization

### Parallel Processing
- **Document Processing**: Process multiple documents in parallel
- **Agent Execution**: Run independent agents concurrently
- **Report Generation**: Generate multiple reports simultaneously

### Caching Strategy
- **Parsed Data**: Cache parsed document data
- **Report Templates**: Cache report templates and configurations
- **Calculation Results**: Cache expensive calculations

### Memory Management
- **Streaming Processing**: Process large documents in chunks
- **Garbage Collection**: Efficient memory cleanup
- **Resource Limits**: Configure memory and CPU limits

## 🔧 Configuration

### Environment Variables
```bash
# Processing Configuration
MAX_DOCUMENT_SIZE=10485760  # 10MB
PARALLEL_PROCESSING_LIMIT=5
CACHE_TTL=3600  # 1 hour
```

### Agent Configuration
```python
# Configure agent parameters
agent_config = {
    'ap_aging': {
        'default_buckets': [0, 30, 60, 90],
        'currency': 'INR',
        'include_paid': False
    },
    'ar_aging': {
        'default_buckets': [0, 30, 60, 90],
        'include_paid': False
    }
}
```

---

**Next Layer**: [Shared Utilities](../shared/README.md) - Common functionality and utilities