# Financial Agents

The Financial Agents module contains specialized AI agents for different financial domains and operations. Each agent is designed to handle specific financial tasks with domain expertise and optimized workflows.

## 🤖 Overview

Financial agents provide specialized capabilities for:
- **Accounts Payable**: Vendor management, invoice processing, aging analysis
- **Accounts Receivable**: Customer management, collections, credit analysis
- **Core Operations**: Base agent functionality and configurable workflows
- **Monitoring & Analysis**: Performance monitoring and financial analysis
- **Reconciliation**: Bank reconciliation and matching operations

## 🏗️ Architecture

```
agents/
├── accounts_payable/     # AP-specific agents
│   ├── ap_aging_agent.py          # AP aging analysis
│   ├── ap_register_agent.py       # AP invoice register
│   ├── ap_overdue_agent.py        # AP overdue analysis
│   └── ap_duplicate_agent.py      # Duplicate invoice detection
├── accounts_receivable/  # AR-specific agents
│   ├── ar_aging_agent.py          # AR aging analysis
│   ├── ar_register_agent.py       # AR invoice register
│   ├── ar_collection_agent.py     # Collection analysis
│   └── dso_agent.py               # Days Sales Outstanding
├── core/                 # Base agent classes
│   ├── base_agent.py              # Base agent implementation
│   ├── configurable_workflow_agent.py  # Configurable workflows
│   ├── rule_based_agent.py        # Rule-based processing
│   ├── universal_report_agent.py  # Universal report generation
│   └── agent_registry.py          # Agent registration and discovery
├── monitoring_analysis/  # Monitoring and analysis
│   ├── performance_monitor.py     # Performance monitoring
│   ├── anomaly_detector.py        # Anomaly detection
│   └── trend_analyzer.py          # Trend analysis
└── reconciliation/       # Reconciliation operations
    ├── bank_reconciliation_agent.py    # Bank reconciliation
    ├── intercompany_reconciliation_agent.py  # Intercompany reconciliation
    └── trial_balance_agent.py     # Trial balance generation
```

## 🏢 Accounts Payable Agents

### AP Aging Agent (`ap_aging_agent.py`)

**Purpose**: Generates comprehensive AP aging analysis reports showing outstanding payables by time buckets.

**Key Features**:
- **Aging Buckets**: 0-30, 31-60, 61-90, 90+ days
- **Vendor Analysis**: Groups by vendor for vendor-specific aging
- **Currency Support**: Multi-currency aging with live exchange rates
- **Trend Analysis**: Shows aging trends over time
- **Export Options**: Excel, CSV, PDF export

**Configuration**:
```python
agent_config = {
    'as_of_date': '2024-12-31',
    'include_paid': False,
    'min_aging_days': 0,
    'currency': 'INR',
    'aging_buckets': [0, 30, 60, 90]
}
```

**Usage**:
```python
from processing_layer.agents.accounts_payable.ap_aging_agent import APAgingAgent

agent = APAgingAgent()
result = agent.execute(
    params={
        'user_id': 'user-123',
        'company_id': 'company-456',
        'as_of_date': '2024-12-31',
        'include_paid': False
    }
)
```

**Output**:
- **Summary Statistics**: Total outstanding, average aging, vendor count
- **Aging Buckets**: Breakdown by time periods with amounts
- **Vendor Details**: Individual vendor aging analysis
- **Trend Analysis**: Historical aging comparison charts
- **Action Items**: Overdue invoices requiring attention

### AP Register Agent (`ap_register_agent.py`)

**Purpose**: Generates complete AP invoice register with all vendor transactions and detailed information.

**Key Features**:
- **Complete Register**: All invoices with full details
- **Vendor Information**: Vendor contact and payment details
- **Status Tracking**: Invoice status (pending, paid, partial)
- **Search and Filter**: Advanced filtering capabilities
- **Export Options**: Multiple export formats

**Configuration**:
```python
agent_config = {
    'date_from': '2024-01-01',
    'date_to': '2024-12-31',
    'vendor_filter': ['vendor-1', 'vendor-2'],
    'status_filter': ['pending', 'paid'],
    'amount_min': 1000,
    'amount_max': 50000
}
```

**Usage**:
```python
from processing_layer.agents.accounts_payable.ap_register_agent import APRegisterAgent

agent = APRegisterAgent()
result = agent.execute(
    params={
        'user_id': 'user-123',
        'company_id': 'company-456',
        'date_from': '2024-01-01',
        'date_to': '2024-12-31'
    }
)
```

**Output**:
- **Invoice Register**: Complete list of all AP invoices
- **Vendor Details**: Vendor information and contact details
- **Payment History**: Payment status and history
- **Aging Information**: Days past due and aging buckets
- **Summary Totals**: Aggregated amounts by status and period

### AP Overdue Agent (`ap_overdue_agent.py`)

**Purpose**: Identifies and analyzes overdue invoices with SLA compliance tracking.

**Key Features**:
- **Overdue Detection**: Automatically identifies overdue invoices
- **SLA Tracking**: Tracks SLA compliance and violations
- **Priority Scoring**: Ranks overdue invoices by priority
- **Escalation Rules**: Configurable escalation rules
- **Notification System**: Automated notifications for overdue items

**Configuration**:
```python
agent_config = {
    'sla_days': 30,
    'priority_rules': {
        'high': {'amount_min': 50000, 'days_overdue_min': 60},
        'medium': {'amount_min': 10000, 'days_overdue_min': 30},
        'low': {'days_overdue_min': 7}
    },
    'escalation_enabled': True
}
```

**Usage**:
```python
from processing_layer.agents.accounts_payable.ap_overdue_agent import APOverdueAgent

agent = APOverdueAgent()
result = agent.execute(
    params={
        'user_id': 'user-123',
        'company_id': 'company-456',
        'sla_days': 30,
        'include_escalated': True
    }
)
```

**Output**:
- **Overdue List**: All overdue invoices with details
- **Priority Ranking**: Priority scores and recommendations
- **SLA Violations**: SLA compliance status and violations
- **Escalation Status**: Escalation rules and status
- **Action Plan**: Recommended actions for each overdue item

### AP Duplicate Agent (`ap_duplicate_agent.py`)

**Purpose**: Detects duplicate invoices using advanced matching algorithms.

**Key Features**:
- **Fuzzy Matching**: Handles typos and formatting differences
- **Multi-field Matching**: Matches on invoice number, amount, date, vendor
- **Confidence Scoring**: Provides confidence scores for matches
- **Duplicate Clustering**: Groups related duplicates together
- **False Positive Filtering**: Reduces false positives with smart filtering

**Configuration**:
```python
agent_config = {
    'matching_fields': ['invoice_number', 'amount', 'date', 'vendor'],
    'confidence_threshold': 0.8,
    'fuzzy_matching': True,
    'date_tolerance': 7,  # days
    'amount_tolerance': 0.01  # 1%
}
```

**Usage**:
```python
from processing_layer.agents.accounts_payable.ap_duplicate_agent import APDuplicateAgent

agent = APDuplicateAgent()
result = agent.execute(
    params={
        'user_id': 'user-123',
        'company_id': 'company-456',
        'confidence_threshold': 0.8,
        'date_range': 'last_90_days'
    }
)
```

**Output**:
- **Duplicate Clusters**: Groups of potentially duplicate invoices
- **Match Details**: Matching fields and confidence scores
- **Risk Assessment**: Risk level for each duplicate cluster
- **Resolution Suggestions**: Recommended actions for duplicates
- **False Positive Filter**: Items filtered out as false positives

## 💰 Accounts Receivable Agents

### AR Aging Agent (`ar_aging_agent.py`)

**Purpose**: Generates AR aging analysis for customer receivables with DSO calculation.

**Key Features**:
- **Customer Aging**: Outstanding receivables by customer
- **DSO Calculation**: Days Sales Outstanding analysis
- **Credit Analysis**: Customer credit utilization
- **Collection Priorities**: Prioritizes collection efforts
- **Trend Analysis**: Historical receivables trends

**Configuration**:
```python
agent_config = {
    'as_of_date': '2024-12-31',
    'include_paid': False,
    'aging_buckets': [0, 30, 60, 90],
    'dso_calculation': True,
    'credit_analysis': True
}
```

**Usage**:
```python
from processing_layer.agents.accounts_receivable.ar_aging_agent import ARAgingAgent

agent = ARAgingAgent()
result = agent.execute(
    params={
        'user_id': 'user-123',
        'company_id': 'company-456',
        'as_of_date': '2024-12-31',
        'include_paid': False
    }
)
```

**Output**:
- **Customer Aging**: Receivables breakdown by customer
- **DSO Analysis**: Days Sales Outstanding metrics
- **Credit Utilization**: Customer credit limit usage
- **Collection Priorities**: Priority-ranked collection targets
- **Trend Analysis**: Historical receivables performance

### AR Register Agent (`ar_register_agent.py`)

**Purpose**: Generates complete AR invoice register with customer transaction details.

**Key Features**:
- **Complete Register**: All customer invoices with details
- **Customer Information**: Customer contact and credit details
- **Payment Tracking**: Payment status and application
- **Credit Management**: Credit limits and utilization
- **Export Options**: Multiple export formats

**Configuration**:
```python
agent_config = {
    'date_from': '2024-01-01',
    'date_to': '2024-12-31',
    'customer_filter': ['customer-1', 'customer-2'],
    'status_filter': ['open', 'paid'],
    'include_credit_info': True
}
```

**Usage**:
```python
from processing_layer.agents.accounts_receivable.ar_register_agent import ARRegisterAgent

agent = ARRegisterAgent()
result = agent.execute(
    params={
        'user_id': 'user-123',
        'company_id': 'company-456',
        'date_from': '2024-01-01',
        'date_to': '2024-12-31'
    }
)
```

**Output**:
- **Invoice Register**: Complete list of all AR invoices
- **Customer Details**: Customer information and credit limits
- **Payment History**: Payment status and application details
- **Aging Information**: Days past due and aging buckets
- **Credit Analysis**: Credit utilization and risk assessment

### AR Collection Agent (`ar_collection_agent.py`)

**Purpose**: Analyzes collection effectiveness and provides collection strategies.

**Key Features**:
- **Collection Analysis**: Collection effectiveness metrics
- **Strategy Recommendations**: Collection strategy suggestions
- **Customer Segmentation**: Customer segmentation for collections
- **Performance Tracking**: Collection performance over time
- **Escalation Rules**: Automated escalation for difficult accounts

**Configuration**:
```python
agent_config = {
    'collection_strategy': 'aggressive',
    'customer_segmentation': True,
    'performance_tracking': True,
    'escalation_rules': {
        'level_1': {'days_overdue': 30, 'action': 'email'},
        'level_2': {'days_overdue': 60, 'action': 'phone'},
        'level_3': {'days_overdue': 90, 'action': 'escalate'}
    }
}
```

**Usage**:
```python
from processing_layer.agents.accounts_receivable.ar_collection_agent import ARCollectionAgent

agent = ARCollectionAgent()
result = agent.execute(
    params={
        'user_id': 'user-123',
        'company_id': 'company-456',
        'collection_strategy': 'aggressive',
        'include_escalation': True
    }
)
```

**Output**:
- **Collection Analysis**: Collection effectiveness metrics
- **Strategy Recommendations**: Tailored collection strategies
- **Customer Segments**: Segmented customers by collection risk
- **Performance Metrics**: Collection performance over time
- **Escalation Status**: Accounts requiring escalation

### DSO Agent (`dso_agent.py`)

**Purpose**: Calculates and analyzes Days Sales Outstanding with trend analysis.

**Key Features**:
- **DSO Calculation**: Accurate DSO calculation
- **Trend Analysis**: Historical DSO trends
- **Benchmarking**: Industry benchmark comparison
- **Root Cause Analysis**: Identifies factors affecting DSO
- **Improvement Recommendations**: Suggestions to improve DSO

**Configuration**:
```python
agent_config = {
    'calculation_method': 'standard',
    'time_period': 'last_12_months',
    'benchmark_comparison': True,
    'root_cause_analysis': True
}
```

**Usage**:
```python
from processing_layer.agents.accounts_receivable.dso_agent import DSOAgent

agent = DSOAgent()
result = agent.execute(
    params={
        'user_id': 'user-123',
        'company_id': 'company-456',
        'time_period': 'last_12_months',
        'benchmark_comparison': True
    }
)
```

**Output**:
- **DSO Metrics**: Current and historical DSO values
- **Trend Analysis**: DSO trends over time
- **Benchmarking**: Comparison with industry standards
- **Root Cause Analysis**: Factors affecting DSO performance
- **Improvement Plan**: Recommendations to improve DSO

## 🔧 Core Agent Classes

### Base Agent (`base_agent.py`)

**Purpose**: Base class providing common functionality for all financial agents.

**Key Features**:
- **Common Interface**: Standardized interface for all agents
- **Error Handling**: Comprehensive error handling and logging
- **Configuration Management**: Centralized configuration handling
- **Execution Tracking**: Track agent execution and performance
- **Result Formatting**: Standardized result formatting

**Usage**:
```python
from processing_layer.agents.core.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self):
        super().__init__("CustomAgent")
    
    def execute(self, input_data=None, params=None):
        # Custom agent logic
        return {
            'status': 'success',
            'message': 'Custom agent executed successfully',
            'data': processed_data
        }
```

### Configurable Workflow Agent (`configurable_workflow_agent.py`)

**Purpose**: Agent that can execute configurable workflows defined by users.

**Key Features**:
- **Workflow Definition**: Define workflows using JSON or YAML
- **Node Execution**: Execute workflow nodes in dependency order
- **Parameter Binding**: Bind parameters to workflow nodes
- **Error Handling**: Handle workflow execution errors
- **Result Aggregation**: Aggregate results from multiple nodes

**Configuration**:
```python
workflow_config = {
    'name': 'Custom Workflow',
    'description': 'Custom financial workflow',
    'nodes': [
        {
            'id': 'node_1',
            'type': 'InvoiceFetchNode',
            'params': {'category': 'purchase'}
        },
        {
            'id': 'node_2',
            'type': 'OutstandingCalculatorNode',
            'params': {}
        }
    ],
    'edges': [
        {'source': 'node_1', 'target': 'node_2'}
    ]
}
```

**Usage**:
```python
from processing_layer.agents.core.configurable_workflow_agent import ConfigurableWorkflowAgent

agent = ConfigurableWorkflowAgent()
result = agent.execute(
    params={
        'workflow_config': workflow_config,
        'user_id': 'user-123',
        'company_id': 'company-456'
    }
)
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
    assert 'summary' in result['data']
    assert 'aging_data' in result['data']
```

### Integration Tests
```python
def test_agent_integration():
    # Test multiple agents working together
    ap_agent = APAgingAgent()
    ar_agent = ARAgingAgent()
    
    # Execute both agents
    ap_result = ap_agent.execute(params={'company_id': 'test-company'})
    ar_result = ar_agent.execute(params={'company_id': 'test-company'})
    
    # Verify results
    assert ap_result['status'] == 'success'
    assert ar_result['status'] == 'success'
    
    # Compare results
    assert 'summary' in ap_result['data']
    assert 'summary' in ar_result['data']
```

## 🚀 Performance Optimization

### Agent Caching
- **Result Caching**: Cache agent results for repeated queries
- **Configuration Caching**: Cache agent configurations
- **Dependency Caching**: Cache frequently used dependencies

### Parallel Execution
- **Independent Agents**: Execute independent agents in parallel
- **Workflow Optimization**: Optimize workflow execution order
- **Resource Management**: Manage resource usage across agents

### Memory Management
- **Agent Lifecycle**: Proper agent lifecycle management
- **Resource Cleanup**: Clean up resources after agent execution
- **Memory Monitoring**: Monitor memory usage during execution

## 🔧 Configuration

### Agent Configuration File
```yaml
agents:
  ap_aging:
    default_buckets: [0, 30, 60, 90]
    currency: INR
    include_paid: false
    max_concurrent: 5
  
  ar_aging:
    default_buckets: [0, 30, 60, 90]
    currency: INR
    include_paid: false
    dso_calculation: true
  
  duplicate_detection:
    confidence_threshold: 0.8
    fuzzy_matching: true
    date_tolerance: 7
    amount_tolerance: 0.01
```

### Environment Variables
```bash
# Agent Configuration
MAX_AGENT_CONCURRENCY=10
AGENT_TIMEOUT=300
AGENT_RETRY_ATTEMPTS=3
AGENT_CACHE_TTL=3600
```

---

**Next Module**: [Document Processing](../document_processing/README.md) - Document ingestion and parsing