# Financial Automation System

A sophisticated multi-layered financial automation platform that leverages AI to process documents, generate reports, and automate financial workflows.

## 🚀 Overview

This system provides end-to-end financial automation with the following key capabilities:

- **Document Processing**: AI-powered parsing of invoices, receipts, and financial documents
- **Natural Language Queries**: Chat-based interface for generating financial reports
- **Multi-Agent System**: Specialized agents for different financial domains (AP, AR, Tax, etc.)
- **Workflow Orchestration**: Visual pipeline execution with configurable nodes
- **Report Generation**: Branded Excel reports with professional formatting
- **Currency Management**: Live exchange rates and multi-currency support

## 🏗️ Architecture

The system follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                      │
├─────────────────────────────────────────────────────────────┤
│              Intelligence Layer (AI Orchestration)          │
├─────────────────────────────────────────────────────────────┤
│             Processing Layer (Agents & Workflows)           │
├─────────────────────────────────────────────────────────────┤
│                Data Layer (PostgreSQL)                      │
├─────────────────────────────────────────────────────────────┤
│                 Shared Utilities                            │
└─────────────────────────────────────────────────────────────┘
```

### Core Layers

#### 1. **Data Layer** (`data_layer/`)
- **Purpose**: Persistent storage and data management
- **Key Components**:
  - `database_manager.py` - PostgreSQL connection and document storage
  - `database_models.py` - SQLAlchemy ORM models
  - `document_repository.py` - Document CRUD operations

#### 2. **Intelligence Layer** (`intelligence_layer/`)
- **Purpose**: AI orchestration, routing, and prompt management
- **Key Components**:
  - `router_prompt_integrator.py` - Connects LLM router with prompt library
  - `orchestrator.py` - Workflow execution engine
  - `domain_classifier.py` - Classifies queries into financial domains
  - `prompt_library.py` - Template-based prompt management

#### 3. **Processing Layer** (`processing_layer/`)
- **Purpose**: Document processing, agent execution, and report generation
- **Key Components**:
  - `document_processing/` - Document ingestion and parsing
  - `agents/` - Specialized financial agents (AP, AR, Tax, etc.)
  - `workflows/` - Configurable workflow nodes
  - `report_generation/` - Excel report generation with branding

#### 4. **Shared Utilities** (`shared/`)
- **Purpose**: Common functionality across all layers
- **Key Components**:
  - `branding/` - Company branding and logo management
  - `calculations/` - Financial calculation engine
  - `llm/` - LLM client management (Groq, Google Gemini)
  - `tools/` - Utility functions and user settings

## 📦 Installation

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Docker (optional, for containerized deployment)

### Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd financial-automation
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your database and API credentials
   ```

4. **Initialize database**:
   ```bash
   python initialize_database.py
   ```

5. **Start the application**:
   ```bash
   python production_api.py
   ```

6. **Access the API**:
   - API Documentation: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/health`

## 🔧 Configuration

### Environment Variables

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/financial_automation

# LLM Configuration
GROQ_API_KEY=your_groq_api_key
GOOGLE_API_KEY=your_google_api_key

# Application Settings
JWT_SECRET=your_jwt_secret_key
UPLOAD_DIR=./data/uploads
OUTPUT_DIR=./data/reports

# Currency Settings
DEFAULT_CURRENCY=INR
EXCHANGE_RATE_API_KEY=your_exchange_rate_api_key
```

### Database Schema

The system uses PostgreSQL with the following main tables:

- **`documents`** - Stores all uploaded financial documents
- **`users`** - User authentication and management
- **`companies`** - Company settings and branding
- **`workflows`** - Workflow execution history
- **`user_settings`** - User preferences and configurations

## 🎯 Usage

### 1. Document Upload

Upload financial documents for processing:

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@invoice.pdf"
```

### 2. Natural Language Queries

Generate reports using natural language:

```bash
curl -X POST "http://localhost:8000/api/v1/chat/query" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me AP aging for last month"}'
```

### 3. Report Generation

Generate specific reports:

```bash
curl -X POST "http://localhost:8000/api/v1/reports/ap-register/simple" \
  -H "Authorization: Bearer <token>"
```

### 4. Company Setup

Configure company branding:

```bash
curl -X PUT "http://localhost:8000/api/v1/company/setup" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "primary_color": "#1976D2",
    "secondary_color": "#424242",
    "default_currency": "INR",
    "company_aliases": ["Company Inc", "Company LLC"]
  }'
```

## 🤖 AI Features

### Multi-Agent System

The system includes specialized agents for different financial domains:

- **AP Agents**: Accounts Payable aging, register, and duplicate detection
- **AR Agents**: Accounts Receivable aging, register, and collection analysis
- **Tax Agent**: GST calculation and tax compliance
- **Analysis Agent**: Revenue trends and expense analysis
- **Reconciliation Agent**: Bank reconciliation and matching

### Natural Language Processing

- **Domain Classification**: Automatically classifies queries into financial domains
- **Variable Extraction**: Extracts dates, entities, and filters from natural language
- **Prompt Integration**: Maps queries to appropriate report templates

### Workflow Orchestration

- **Visual Pipelines**: See workflow execution in real-time
- **Configurable Nodes**: Mix and match processing steps
- **Error Handling**: Automatic retry and fallback mechanisms

## 📊 Report Types

### Accounts Payable Reports
- **AP Aging**: Aging analysis by time buckets (0-30, 31-60, 61-90, 90+ days)
- **AP Register**: Complete invoice register with vendor details
- **AP Overdue SLA**: Overdue invoices with SLA compliance tracking

### Accounts Receivable Reports
- **AR Aging**: Customer aging analysis
- **AR Register**: Customer invoice register
- **DSO Analysis**: Days Sales Outstanding analysis

### Analysis Reports
- **Revenue Trends**: Time-series revenue analysis
- **Expense Analysis**: Categorical expense breakdown
- **Budget Variance**: Budget vs actual analysis

## 🔐 Security

- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access**: User and company-level permissions
- **Data Encryption**: Sensitive data encryption at rest
- **Audit Logging**: Complete audit trail of all operations

## 🚀 Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Production Deployment

1. **Environment Setup**:
   - Configure production database
   - Set up SSL certificates
   - Configure load balancer

2. **Scaling**:
   - Use multiple API instances
   - Configure database connection pooling
   - Implement caching layer

3. **Monitoring**:
   - Set up health checks
   - Configure logging aggregation
   - Monitor performance metrics

## 🧪 Testing

### Unit Tests
```bash
python -m pytest tests/unit/
```

### Integration Tests
```bash
python -m pytest tests/integration/
```

### End-to-End Tests
```bash
python -m pytest tests/e2e/
```

## 📚 API Documentation

Comprehensive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔗 Integration

### Webhook Support
The system supports webhooks for:
- Document processing completion
- Report generation completion
- Workflow execution status

### Third-Party Integrations
- **Accounting Software**: QuickBooks, Xero integration
- **Payment Gateways**: Stripe, PayPal integration
- **Cloud Storage**: AWS S3, Google Cloud Storage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [API Docs](http://localhost:8000/docs)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Email**: support@yourcompany.com

## 🙏 Acknowledgments

- Built with FastAPI and PostgreSQL
- AI capabilities powered by Groq and Google Gemini
- Excel generation with openpyxl
- Frontend integration with Streamlit

---

**Made with ❤️ for financial automation**