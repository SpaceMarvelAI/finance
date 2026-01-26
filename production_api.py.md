# Production API Documentation

## File Overview

**File**: `production_api.py`
**Purpose**: Main FastAPI application server for the Financial Automation System
**Version**: 3.1.0
**Status**: Production-ready

## 🚀 Quick Start

### Starting the Server
```bash
python production_api.py
```

### Access Points
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Root Endpoint**: http://localhost:8000/

## 📋 API Endpoints

### Authentication Endpoints

#### POST /api/v1/auth/register
Register a new user and company.

**Request Body**:
```json
{
    "email": "user@example.com",
    "password": "securepassword",
    "full_name": "John Doe",
    "company_name": "Example Company"
}
```

**Response**:
```json
{
    "status": "success",
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "user_id": "user-uuid",
    "company_id": "company-uuid",
    "company_name": "Example Company"
}
```

#### POST /api/v1/auth/login
Authenticate user and get access token.

**Request Body**:
```json
{
    "email": "user@example.com",
    "password": "securepassword"
}
```

**Response**:
```json
{
    "status": "success",
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "user_id": "user-uuid",
    "company_id": "company-uuid",
    "company_name": "Example Company"
}
```

### Company Management Endpoints

#### PUT /api/v1/company/setup
Update company branding and settings.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request Body**:
```json
{
    "primary_color": "#1976D2",
    "secondary_color": "#424242",
    "accent_color": "#FF5722",
    "default_currency": "INR",
    "company_aliases": ["Company Inc", "Company LLC"]
}
```

**Response**:
```json
{
    "status": "success",
    "message": "Company setup updated",
    "company": {
        "name": "Example Company",
        "aliases": ["Company Inc", "Company LLC"],
        "logo_url": "/static/logos/company-uuid_logo.png",
        "primary_color": "#1976D2",
        "secondary_color": "#424242",
        "currency": "INR"
    }
}
```

#### POST /api/v1/company/logo
Upload company logo.

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request**: Form data with file field `file`

**Response**:
```json
{
    "status": "success",
    "logo_url": "/static/logos/company-uuid_logo.png",
    "file_size_kb": 15.25,
    "file_type": ".png",
    "message": "Logo uploaded successfully"
}
```

### Document Management Endpoints

#### POST /api/v1/documents/upload
Upload financial documents for processing.

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request**: Form data with file field `file`

**Response**:
```json
{
    "status": "success",
    "document_id": "doc-uuid",
    "category": "purchase",
    "party": "Vendor Name",
    "extracted_data": {
        "invoice_number": "INV-2024-001",
        "invoice_date": "2024-12-01",
        "grand_total": 1000.0,
        "vendor_name": "Vendor Name"
    }
}
```

#### GET /api/v1/documents
List uploaded documents.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Query Parameters**:
- `limit`: Number of documents to return (default: 100)

**Response**:
```json
{
    "status": "success",
    "count": 5,
    "documents": [
        {
            "id": "doc-uuid-1",
            "file_name": "invoice.pdf",
            "document_type": "invoice",
            "category": "purchase",
            "uploaded_at": "2024-12-31T12:00:00"
        }
    ]
}
```

### Chat and Query Endpoints

#### POST /api/v1/chat/query
Process natural language queries and generate reports.

**Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body**:
```json
{
    "query": "Show me AP aging for last month"
}
```

**Response**:
```json
{
    "status": "success",
    "workflow": {
        "id": "workflow-uuid",
        "name": "AP Aging Report",
        "query": "Show me AP aging for last month",
        "agent": "APAgingAgent",
        "domain": "APLayer",
        "report_type": "ap_aging",
        "status": "completed",
        "nodes": [
            {
                "id": "node_1",
                "type": "InvoiceFetchNode",
                "name": "Fetch Invoices",
                "status": "completed",
                "data": {
                    "label": "Fetch Invoices",
                    "params": {"category": "purchase"}
                }
            }
        ],
        "edges": [
            {"source": "node_1", "target": "node_2"}
        ],
        "created_at": "2024-12-31T12:00:00"
    },
    "report": {
        "file_path": "/data/reports/AP_Aging_20241231_120000.xlsx",
        "download_url": "/api/v1/reports/download/AP_Aging_20241231_120000.xlsx"
    },
    "execution": {
        "time_ms": 1500,
        "nodes_executed": 4
    }
}
```

### Report Endpoints

#### GET /api/v1/reports/download/{filename}
Download generated reports.

**Response**: File download (Excel, PDF, or CSV)

#### POST /api/v1/reports/ap-register/simple
Generate simple AP register report.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**:
```json
{
    "status": "success",
    "file_path": "/data/reports/ap_register_20241231_120000.xlsx",
    "download_url": "/api/v1/reports/download/ap_register_20241231_120000.xlsx",
    "record_count": 50,
    "total_amount": 100000.0
}
```

#### GET /api/v1/workflows
List workflow execution history.

**Headers**:
```
Authorization: Bearer <access_token>
```

**Query Parameters**:
- `limit`: Number of workflows to return (default: 50)

**Response**:
```json
{
    "status": "success",
    "count": 3,
    "workflows": [
        {
            "id": "workflow-uuid",
            "name": "AP Aging Report",
            "query": "Show me AP aging for last month",
            "type": "ap_aging",
            "status": "completed",
            "created_at": "2024-12-31T12:00:00",
            "output_file": "/data/reports/AP_Aging_20241231_120000.xlsx"
        }
    ]
}
```

### System Endpoints

#### GET /api/v1/agents
List available agents.

**Response**:
```json
{
    "status": "success",
    "count": 8,
    "agents": {
        "ap_aging": "APAgingAgent",
        "ap_register": "APRegisterAgent",
        "ap_overdue": "APOverdueAgent",
        "ap_duplicate": "APDuplicateAgent",
        "ar_aging": "ARAgingAgent",
        "ar_register": "ARRegisterAgent",
        "ar_collection": "ARCollectionAgent",
        "dso": "DSOAgent"
    }
}
```

#### GET /api/v1/nodes
List available workflow nodes.

**Response**:
```json
{
    "status": "success",
    "count": 15,
    "nodes": [
        "InvoiceFetchNode",
        "OutstandingCalculatorNode",
        "AgingCalculatorNode",
        "FilterNode",
        "GroupingNode",
        "SummaryNode",
        "ExcelGeneratorNode"
    ]
}
```

#### GET /api/v1/debug/documents
Debug endpoint to check documents (requires authentication).

**Headers**:
```
Authorization: Bearer <access_token>
```

**Response**:
```json
{
    "company_id": "company-uuid",
    "documents": [
        {
            "id": "doc-uuid",
            "file_name": "invoice.pdf",
            "category": "purchase",
            "vendor_name": "Vendor Name",
            "customer_name": null,
            "grand_total": 1000.0,
            "status": "processed"
        }
    ],
    "categories": [
        {"category": "purchase", "count": 5},
        {"category": "sales", "count": 3}
    ]
}
```

## 🔐 Authentication

The API uses JWT (JSON Web Tokens) for authentication. All endpoints except `/`, `/health`, and `/docs` require a valid JWT token.

### Token Format
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Token Expiration
- Default: 24 hours
- Configurable via `TOKEN_EXPIRE_HOURS` environment variable

## 🏗️ Architecture

### Layer Integration
The API integrates all system layers:

1. **Data Layer**: Database operations via `DatabaseManager`
2. **Intelligence Layer**: AI processing via `RouterPromptIntegrator`
3. **Processing Layer**: Document processing and agent execution
4. **Shared Utilities**: Configuration, logging, and utilities

### Key Components

#### Database Models
- `User`: User authentication and management
- `Company`: Company settings and branding
- `Document`: Financial document storage
- `Workflow`: Workflow execution history

#### Services Integration
- **Document Processing**: `DocumentProcessingService`
- **AI Routing**: `RouterPromptIntegrator`
- **Agent Execution**: Specialized financial agents
- **Report Generation**: Branded Excel reports

## ⚙️ Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/financial_automation

# Authentication
JWT_SECRET=your-secret-key-change-in-production
TOKEN_EXPIRE_HOURS=24

# Application
API_HOST=0.0.0.0
API_PORT=8000

# File Paths
UPLOAD_DIR=./data/uploads
OUTPUT_DIR=./data/reports
```

### CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

## 🚀 Deployment

### Production Deployment
1. **Environment Setup**:
   ```bash
   # Set production environment variables
   export DATABASE_URL="postgresql://user:pass@prod-db:5432/financial_automation"
   export JWT_SECRET="production-secret-key"
   export API_HOST="0.0.0.0"
   export API_PORT=8000
   ```

2. **SSL/TLS**:
   ```bash
   # Use reverse proxy (nginx) for SSL termination
   # Configure SSL certificates
   ```

3. **Process Management**:
   ```bash
   # Use process manager (systemd, supervisor, etc.)
   # Configure auto-restart and monitoring
   ```

4. **Load Balancing**:
   ```bash
   # Deploy multiple instances
   # Use load balancer for traffic distribution
   ```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "production_api.py"]
```

### Health Checks
The `/health` endpoint provides system status:
```json
{
    "status": "healthy",
    "timestamp": "2024-12-31T12:00:00",
    "agents": 8,
    "nodes": 15
}
```

## 🧪 Testing

### Manual Testing
```bash
# Test authentication
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass","full_name":"Test User","company_name":"Test Company"}'

# Test document upload
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "Authorization: Bearer <token>" \
  -F "file=@invoice.pdf"

# Test chat query
curl -X POST "http://localhost:8000/api/v1/chat/query" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"query":"Show me AP aging for last month"}'
```

### Automated Testing
```python
import requests

def test_api_endpoints():
    # Test health endpoint
    response = requests.get("http://localhost:8000/health")
    assert response.status_code == 200
    
    # Test authentication
    auth_response = requests.post(
        "http://localhost:8000/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpass"}
    )
    assert auth_response.status_code == 200
    token = auth_response.json()["access_token"]
    
    # Test protected endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("http://localhost:8000/api/v1/documents", headers=headers)
    assert response.status_code == 200
```

## 📊 Monitoring

### Metrics
The API provides built-in metrics:
- **Agent Count**: Number of available agents
- **Node Count**: Number of available workflow nodes
- **Execution Time**: Workflow execution duration
- **Error Rate**: Failed request percentage

### Logging
Comprehensive logging is enabled:
- **Request Logging**: All incoming requests
- **Error Logging**: Detailed error information
- **Performance Logging**: Execution times and bottlenecks
- **Security Logging**: Authentication and authorization events

### Health Monitoring
Monitor these endpoints for system health:
- `/health` - System status
- `/api/v1/agents` - Agent availability
- `/api/v1/nodes` - Node availability
- Database connectivity

## 🔒 Security

### Authentication Security
- **JWT Tokens**: Secure token-based authentication
- **Password Hashing**: BCrypt for password security
- **Token Expiration**: Automatic token expiration
- **Secure Headers**: Security headers configuration

### Input Validation
- **File Upload**: File type and size validation
- **JSON Input**: Schema validation for all JSON inputs
- **SQL Injection**: Parameterized queries prevent injection
- **XSS Protection**: Input sanitization

### Production Security
- **Environment Variables**: Sensitive data in environment variables
- **HTTPS**: SSL/TLS for all production traffic
- **CORS**: Proper CORS configuration
- **Rate Limiting**: API rate limiting (implement as needed)

## 🚨 Error Handling

### Common Errors
- **401 Unauthorized**: Invalid or missing JWT token
- **400 Bad Request**: Invalid request format or parameters
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server-side errors

### Error Response Format
```json
{
    "detail": "Error description"
}
```

### Debug Mode
Enable debug mode for development:
```python
if __name__ == "__main__":
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT, reload=True)
```

## 📈 Performance

### Optimization Features
- **Connection Pooling**: Database connection pooling
- **File Streaming**: Efficient file upload/download
- **Caching**: Agent and node caching
- **Async Processing**: Non-blocking operations

### Performance Monitoring
- **Response Times**: Monitor API response times
- **Database Queries**: Monitor query performance
- **Memory Usage**: Monitor memory consumption
- **CPU Usage**: Monitor CPU utilization

### Scaling Recommendations
- **Horizontal Scaling**: Deploy multiple API instances
- **Database Scaling**: Use read replicas for read-heavy workloads
- **Caching**: Implement Redis or similar for caching
- **CDN**: Use CDN for static file serving

---

**Next File**: [Database Manager](data_layer/database/database_manager.py.md) - Database operations and management