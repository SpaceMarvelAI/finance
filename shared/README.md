# Shared Utilities

The Shared Utilities layer provides common functionality and utilities used across all layers of the Financial Automation System. This layer ensures consistency, reusability, and maintainability throughout the application.

## 🔧 Overview

The Shared Utilities layer provides:
- **Configuration Management**: Centralized configuration and settings
- **LLM Integration**: Unified interface for AI model interactions
- **Branding Management**: Company branding and logo handling
- **Financial Calculations**: Common financial calculation functions
- **Currency Management**: Multi-currency support and exchange rates
- **User Settings**: User preferences and configurations
- **Logging and Monitoring**: Centralized logging and monitoring

## 🏗️ Architecture

```
shared/
├── config/              # Configuration management
│   ├── config_manager.py         # Main configuration manager
│   ├── logging_config.py         # Logging configuration
│   └── settings.py              # Application settings
├── llm/                 # AI model integration
│   ├── groq_client.py           # Groq API client
│   └── gemini_client.py         # Google Gemini client
├── branding/            # Company branding
│   ├── company_branding.py      # Company branding management
│   ├── api_branding.py          # API response branding
│   └── assets/                  # Branding assets
├── calculations/        # Financial calculations
│   ├── calculation_engine.py    # Core calculation engine
│   └── financial_formulas.py    # Financial formula implementations
├── tools/               # Utility functions
│   ├── user_settings.py         # User settings management
│   ├── mcp_financial_tools.py   # MCP financial tools
│   └── file_utils.py            # File utility functions
└── utils/              # General utilities
    ├── currency_converter.py    # Currency conversion
    ├── live_exchange_rates.py   # Live exchange rate fetching
    ├── migrate_currency.py      # Currency migration utilities
    └── date_utils.py            # Date manipulation utilities
```

## ⚙️ Configuration Management

### Configuration Manager (`config/config_manager.py`)

**Purpose**: Central configuration management system that handles application settings and environment variables.

**Key Features**:
- **Environment Variables**: Load configuration from environment variables
- **File-based Config**: Support for configuration files
- **Validation**: Validate configuration values
- **Caching**: Cache configuration for performance
- **Hot Reload**: Support for configuration updates without restart

**Usage**:
```python
from shared.config.config_manager import ConfigManager

# Initialize configuration manager
config = ConfigManager()

# Get configuration values
database_url = config.get('DATABASE_URL')
api_key = config.get('GROQ_API_KEY')
max_workers = config.get('MAX_WORKERS', default=10)

# Set configuration values
config.set('DEBUG_MODE', True)
config.set('LOG_LEVEL', 'INFO')
```

**Configuration Categories**:
- **Database**: Connection strings, timeouts, pool sizes
- **LLM**: API keys, model configurations, rate limits
- **Processing**: Document limits, parallel processing settings
- **Security**: JWT secrets, encryption keys, CORS settings
- **Branding**: Company colors, logo URLs, default currency

### Logging Configuration (`config/logging_config.py`)

**Purpose**: Centralized logging configuration with structured logging support.

**Key Features**:
- **Multiple Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Structured Logging**: JSON-formatted logs for better parsing
- **Log Rotation**: Automatic log rotation to prevent disk space issues
- **Multiple Outputs**: Console, file, and external logging services
- **Performance Monitoring**: Log execution times and performance metrics

**Usage**:
```python
from shared.config.logging_config import get_logger

# Get logger for module
logger = get_logger(__name__)

# Log messages
logger.info("Document processing started", extra={
    'document_id': 'doc-123',
    'file_name': 'invoice.pdf'
})

logger.error("Processing failed", exc_info=True, extra={
    'step': 'parsing',
    'error_code': 'PARSING_ERROR'
})
```

**Log Format**:
```json
{
    "timestamp": "2024-12-31T12:00:00.000Z",
    "level": "INFO",
    "module": "document_processing",
    "message": "Document processed successfully",
    "extra": {
        "document_id": "doc-123",
        "processing_time_ms": 1500,
        "file_size": 1024000
    }
}
```

## 🤖 LLM Integration

### Groq Client (`llm/groq_client.py`)

**Purpose**: Unified client for Groq API integration with rate limiting and error handling.

**Key Features**:
- **Multiple Models**: Support for different Groq models (Llama, Mixtral, etc.)
- **Rate Limiting**: Automatic rate limiting and retry logic
- **Caching**: Cache responses to reduce API calls
- **Error Handling**: Comprehensive error handling and fallbacks
- **Metrics**: Track API usage and performance

**Usage**:
```python
from shared.llm.groq_client import get_groq_client

# Get Groq client
client = get_groq_client(model="llama3-70b-8192")

# Make API call
response = client.chat_completion(
    messages=[
        {"role": "user", "content": "Analyze this invoice data"}
    ],
    temperature=0.1,
    max_tokens=1000
)

print(f"Response: {response['choices'][0]['message']['content']}")
```

**Configuration**:
```python
# Configure client
client_config = {
    'api_key': 'your-groq-api-key',
    'model': 'llama3-70b-8192',
    'max_tokens': 2000,
    'temperature': 0.1,
    'rate_limit': 100,  # requests per minute
    'timeout': 30,      # seconds
    'retry_attempts': 3
}
```

### Gemini Client (`llm/gemini_client.py`)

**Purpose**: Client for Google Gemini API integration.

**Key Features**:
- **Gemini Models**: Support for Gemini Pro and other models
- **Safety Settings**: Configurable safety and content filtering
- **Multimodal**: Support for text and image inputs
- **Streaming**: Support for streaming responses
- **Cost Tracking**: Track API costs and usage

**Usage**:
```python
from shared.llm.gemini_client import get_gemini_client

# Get Gemini client
client = get_gemini_client(model="gemini-pro")

# Generate content
response = client.generate_content(
    prompt="Analyze this financial document",
    image_path="/path/to/document.pdf"
)

print(f"Analysis: {response.text}")
```

## 🎨 Branding Management

### Company Branding (`branding/company_branding.py`)

**Purpose**: Manages company branding information including colors, logos, and company details.

**Key Features**:
- **Brand Colors**: Primary, secondary, and accent colors
- **Logo Management**: Logo upload and retrieval
- **Company Information**: Company name, address, contact details
- **Brand Consistency**: Ensure consistent branding across reports
- **Validation**: Validate brand assets and colors

**Usage**:
```python
from shared.branding.company_branding import CompanyBranding

# Initialize branding
branding = CompanyBranding(company_id='company-123')

# Set company branding
branding.update_branding({
    'primary_color': '#1976D2',
    'secondary_color': '#424242',
    'accent_color': '#FF5722',
    'company_name': 'Your Company',
    'logo_url': '/path/to/logo.png'
})

# Get branding for reports
brand_info = branding.get_branding_for_reports()
print(f"Primary Color: {brand_info['primary_color']}")
```

**Brand Configuration**:
```python
brand_config = {
    'primary_color': '#1976D2',      # Main brand color
    'secondary_color': '#424242',    # Secondary color
    'accent_color': '#FF5722',       # Accent color
    'font_family': 'Arial, sans-serif',
    'font_size': '12px',
    'logo_url': '/assets/logo.png',
    'company_name': 'Your Company',
    'company_address': '123 Business St, City, State',
    'company_phone': '+1-555-123-4567',
    'company_email': 'info@yourcompany.com'
}
```

### API Branding (`branding/api_branding.py`)

**Purpose**: Manages branding for API responses and documentation.

**Key Features**:
- **API Documentation**: Branded API documentation
- **Response Headers**: Custom response headers with branding
- **Error Messages**: Branded error messages
- **CORS Configuration**: CORS settings with branding
- **Rate Limiting**: Branded rate limiting responses

**Usage**:
```python
from shared.branding.api_branding import APIBranding

# Configure API branding
api_branding = APIBranding(company_id='company-123')

# Apply branding to FastAPI app
app = FastAPI()
api_branding.apply_to_app(app)

# Custom error responses
@app.exception_handler(HTTPException)
async def branded_error_handler(request, exc):
    return api_branding.format_error_response(exc)
```

## 💰 Financial Calculations

### Calculation Engine (`calculations/calculation_engine.py`)

**Purpose**: Core engine for financial calculations with support for complex financial formulas.

**Key Features**:
- **Aging Calculations**: AP/AR aging bucket calculations
- **Currency Conversion**: Real-time currency conversion
- **Tax Calculations**: GST, VAT, and other tax calculations
- **Interest Calculations**: Simple and compound interest
- **Amortization**: Loan amortization schedules
- **Depreciation**: Asset depreciation calculations

**Usage**:
```python
from shared.calculations.calculation_engine import CalculationEngine

# Initialize calculation engine
engine = CalculationEngine()

# Calculate aging
aging_result = engine.calculate_aging(
    invoice_date='2024-12-01',
    due_date='2024-12-31',
    as_of_date='2024-12-31'
)

print(f"Aging Days: {aging_result['aging_days']}")
print(f"Aging Bucket: {aging_result['bucket']}")

# Currency conversion
converted_amount = engine.convert_currency(
    amount=1000.0,
    from_currency='USD',
    to_currency='INR',
    date='2024-12-31'
)
```

**Supported Calculations**:
- **Aging Analysis**: Days past due, aging buckets
- **Currency Operations**: Conversion, revaluation
- **Tax Calculations**: GST, VAT, sales tax
- **Interest Calculations**: Simple, compound, daily rates
- **Financial Ratios**: Current ratio, quick ratio, DSO
- **Amortization**: Loan schedules, payment calculations

### Financial Formulas (`calculations/financial_formulas.py`)

**Purpose**: Library of common financial formulas and calculations.

**Key Features**:
- **Ratio Calculations**: Financial ratio formulas
- **Time Value**: Present value, future value calculations
- **Risk Metrics**: Standard deviation, variance
- **Performance Metrics**: ROI, ROE, ROA
- **Statistical Functions**: Mean, median, standard deviation

**Usage**:
```python
from shared.calculations.financial_formulas import FinancialFormulas

# Calculate financial ratios
ratios = FinancialFormulas()

current_ratio = ratios.current_ratio(
    current_assets=100000,
    current_liabilities=50000
)

print(f"Current Ratio: {current_ratio}")

# Calculate ROI
roi = ratios.return_on_investment(
    net_profit=25000,
    investment_cost=100000
)

print(f"ROI: {roi:.2%}")
```

## 💱 Currency Management

### Currency Converter (`utils/currency_converter.py`)

**Purpose**: Handles currency conversion with support for multiple exchange rate sources.

**Key Features**:
- **Multiple Sources**: Support for different exchange rate APIs
- **Historical Rates**: Access to historical exchange rates
- **Caching**: Cache exchange rates to reduce API calls
- **Fallback**: Fallback mechanisms for rate availability
- **Validation**: Validate currency codes and rates

**Usage**:
```python
from shared.utils.currency_converter import CurrencyConverter

# Initialize converter
converter = CurrencyConverter()

# Convert currency
result = converter.convert(
    amount=1000.0,
    from_currency='USD',
    to_currency='INR',
    date='2024-12-31'
)

print(f"Converted Amount: {result}")

# Get exchange rate
rate = converter.get_rate('USD', 'INR', '2024-12-31')
print(f"Exchange Rate: {rate}")
```

**Supported Currencies**:
- **Major Currencies**: USD, EUR, GBP, JPY, INR, CAD, AUD
- **Cryptocurrencies**: BTC, ETH, USDT (limited support)
- **Custom Currencies**: Support for custom currency definitions

### Live Exchange Rates (`utils/live_exchange_rates.py`)

**Purpose**: Fetches live exchange rates from external APIs with caching and fallback.

**Key Features**:
- **Real-time Rates**: Fetch live exchange rates
- **Multiple Providers**: Support for multiple rate providers
- **Caching**: Cache rates to reduce API calls
- **Historical Data**: Access to historical rate data
- **Rate Alerts**: Monitor rate changes and alerts

**Usage**:
```python
from shared.utils.live_exchange_rates import get_rate_provider

# Get rate provider
provider = get_rate_provider()

# Get current rate
current_rate = provider.get_rate('USD', 'INR')
print(f"Current Rate: {current_rate}")

# Get rate for specific date
historical_rate = provider.get_rate_for_date('USD', 'INR', '2024-12-31')
print(f"Historical Rate: {historical_rate}")

# Convert with live rates
converted = provider.convert(1000.0, 'USD', 'INR')
print(f"Converted: {converted}")
```

**Rate Providers**:
- **ExchangeRate-API**: Free tier available
- **Open Exchange Rates**: Premium rates
- **Fixer.io**: Historical data support
- **Custom Provider**: Support for custom rate sources

## 👤 User Settings

### User Settings Manager (`tools/user_settings.py`)

**Purpose**: Manages user preferences, settings, and configurations.

**Key Features**:
- **User Preferences**: Store user-specific preferences
- **Default Settings**: Manage default application settings
- **Settings Validation**: Validate user settings
- **Settings Import/Export**: Import and export user settings
- **Multi-tenancy**: Support for multi-tenant settings

**Usage**:
```python
from shared.tools.user_settings import get_settings_manager

# Get settings manager
settings_mgr = get_settings_manager()

# Get user settings
user_settings = settings_mgr.get_user_settings('user-123')

# Update user settings
settings_mgr.update_user_settings('user-123', {
    'default_currency': 'INR',
    'date_format': 'DD/MM/YYYY',
    'time_zone': 'Asia/Kolkata',
    'notifications_enabled': True
})

# Get default settings
defaults = settings_mgr.get_default_settings()
```

**Settings Categories**:
- **Display Settings**: Date format, time zone, language
- **Notification Settings**: Email, SMS, push notifications
- **Report Settings**: Default report formats, export options
- **Security Settings**: Password policies, session timeout
- **Integration Settings**: Third-party integrations, API keys

## 🧪 Testing

### Unit Tests
```python
import pytest
from shared.config.config_manager import ConfigManager

def test_config_manager():
    config = ConfigManager()
    
    # Test getting configuration
    config.set('TEST_KEY', 'test_value')
    assert config.get('TEST_KEY') == 'test_value'
    
    # Test default values
    assert config.get('NON_EXISTENT_KEY', default='default') == 'default'
```

### Integration Tests
```python
def test_currency_conversion():
    from shared.utils.currency_converter import CurrencyConverter
    
    converter = CurrencyConverter()
    
    # Test currency conversion
    result = converter.convert(100.0, 'USD', 'INR')
    assert result > 0
    assert isinstance(result, (int, float))
```

## 🔧 Configuration

### Environment Variables
```bash
# Configuration
CONFIG_FILE_PATH=./config/app.json
LOG_LEVEL=INFO
LOG_FILE_PATH=./logs/app.log

# LLM Configuration
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key

# Currency Configuration
EXCHANGE_RATE_API_KEY=your_exchange_rate_api_key
DEFAULT_CURRENCY=INR
CURRENCY_CACHE_TTL=3600

# Branding Configuration
COMPANY_NAME=Your Company
PRIMARY_COLOR=#1976D2
SECONDARY_COLOR=#424242
LOGO_URL=/assets/logo.png
```

### Configuration File Example
```json
{
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "financial_automation",
        "user": "postgres",
        "password": "password",
        "pool_size": 10
    },
    "llm": {
        "provider": "groq",
        "model": "llama3-70b-8192",
        "max_tokens": 2000,
        "temperature": 0.1
    },
    "currency": {
        "default": "INR",
        "providers": ["exchangerate-api", "openexchangerates"],
        "cache_ttl": 3600
    },
    "branding": {
        "primary_color": "#1976D2",
        "secondary_color": "#424242",
        "font_family": "Arial, sans-serif"
    }
}
```

## 🔒 Security

### Configuration Security
- **Environment Variables**: Store sensitive data in environment variables
- **Encryption**: Encrypt sensitive configuration values
- **Access Control**: Restrict access to configuration files
- **Audit Logging**: Log configuration changes

### Currency Security
- **Rate Validation**: Validate exchange rates for anomalies
- **Source Verification**: Verify exchange rate source authenticity
- **Fallback Mechanisms**: Handle rate provider failures securely

---

**Integration**: This layer integrates with all other layers to provide consistent functionality across the application.