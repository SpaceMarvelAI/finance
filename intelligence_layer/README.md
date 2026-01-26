# Intelligence Layer

The Intelligence Layer provides AI orchestration, natural language processing, and intelligent routing capabilities for the Financial Automation System. It acts as the brain of the system, interpreting user queries and coordinating complex workflows.

## 🧠 Overview

The Intelligence Layer is responsible for:
- **Natural Language Processing**: Understanding and interpreting user queries
- **Domain Classification**: Categorizing queries into financial domains
- **Workflow Orchestration**: Coordinating multi-step processing workflows
- **Prompt Management**: Managing and executing AI prompts
- **Agent Coordination**: Managing specialized financial agents

## 🏗️ Architecture

```
intelligence_layer/
├── orchestration/        # Workflow execution and coordination
│   ├── orchestrator.py              # Main orchestrator
│   ├── enhanced_orchestrator.py     # Enhanced workflow engine
│   ├── workflow_planner_agent.py    # Workflow planning
│   ├── master_orchestrator_agent.py # Master coordination
│   └── financial_report_system.py   # Report generation system
├── parsing/             # Natural language understanding
│   ├── domain_classifier.py         # Query domain classification
│   ├── enhanced_intent_parser.py    # Intent extraction
│   ├── intent_parser_agent.py       # Intent parsing agent
│   └── variable_extractor.py        # Variable extraction
├── prompts/             # Prompt library and management
│   ├── prompt_library.py            # Template-based prompts
│   └── prompt_templates/            # Individual prompt templates
└── routing/             # Query routing and integration
    └── router_prompt_integrator.py  # Router integration
```

## 🤖 Key Components

### Router-Prompt Integration (`router_prompt_integrator.py`)

**Purpose**: Connects the LLM router with the prompt library to provide seamless report generation from natural language queries.

**Key Features**:
- **Query Processing Pipeline**: User query → Domain → Variables → Prompt → Report
- **Domain Classification**: Automatically classifies queries into financial domains
- **Variable Extraction**: Extracts dates, entities, and filters from natural language
- **Prompt Selection**: Maps domains to appropriate prompt templates
- **Agent Coordination**: Routes queries to specialized agents

**Usage**:
```python
from intelligence_layer.routing.router_prompt_integrator import RouterPromptIntegrator

integrator = RouterPromptIntegrator()

# Process natural language query
result = integrator.process_query(
    query="Show me AP aging for last month",
    context={'user_id': 'user-123', 'company_id': 'company-456'}
)

print(f"Domain: {result['domain']}")
print(f"Agent: {result['agent']}")
print(f"Prompt: {result['rendered_prompt']}")
```

**Processing Flow**:
1. **Domain Classification**: Uses `DomainClassifier` to identify financial domain
2. **Variable Extraction**: Uses `VariableExtractor` to extract parameters
3. **Prompt Selection**: Maps domain to appropriate prompt template
4. **Prompt Rendering**: Injects variables into prompt template
5. **Agent Routing**: Routes to specialized agent for execution

### Domain Classifier (`domain_classifier.py`)

**Purpose**: Classifies user queries into specific financial domains to determine appropriate processing.

**Supported Domains**:
- **APLayer**: Accounts Payable operations
- **ARLayer**: Accounts Receivable operations
- **FinanceLayer**: General financial operations
- **ReportLayer**: Report generation
- **AnalysisLayer**: Financial analysis
- **ReconciliationLayer**: Bank reconciliation
- **ComplianceLayer**: Compliance and audit
- **CashFlowLayer**: Cash flow management
- **TaxLayer**: Tax calculations
- **BudgetLayer**: Budget management
- **AlertLayer**: Notifications and alerts

**Classification Process**:
```python
from intelligence_layer.parsing.domain_classifier import DomainClassifier

classifier = DomainClassifier()

# Classify query
result = classifier.classify("Generate AP aging report for Q4")
print(f"Domain: {result['domain']}")
print(f"Confidence: {result['confidence']:.2%}")
```

**Algorithm**:
- Uses keyword matching and pattern recognition
- Supports fuzzy matching for robust classification
- Returns confidence scores for classification quality
- Handles ambiguous queries gracefully

### Enhanced Intent Parser (`enhanced_intent_parser.py`)

**Purpose**: Extracts structured intent and variables from natural language queries.

**Extracted Components**:
- **Time**: Date ranges, periods, relative dates
- **Entities**: Vendors, customers, departments
- **Filters**: Amount ranges, status filters, category filters
- **Output**: Desired output format and options
- **Analysis**: Specific analysis requirements

**Usage**:
```python
from intelligence_layer.parsing.enhanced_intent_parser import EnhancedIntentParser

parser = EnhancedIntentParser()

# Parse query intent
result = parser.parse("Show me invoices from AWS over $5000 in December")
print(f"Report Type: {result['report_type']}")
print(f"Variables: {result['variables']}")
```

**Variable Extraction**:
- **Time Variables**: `start_date`, `end_date`, `relative_date`
- **Entity Variables**: `vendor_ids`, `customer_ids`, `department_ids`
- **Filter Variables**: `amount_min`, `amount_max`, `status`
- **Output Variables**: `output_format`, `include_details`

### Workflow Planner Agent (`workflow_planner_agent.py`)

**Purpose**: Plans and generates workflow definitions for complex multi-step operations.

**Key Features**:
- **Visual Pipeline Generation**: Creates workflow graphs with nodes and edges
- **Node Selection**: Chooses appropriate processing nodes
- **Parameter Configuration**: Sets node parameters based on requirements
- **Error Handling**: Plans for error scenarios and fallbacks

**Usage**:
```python
from intelligence_layer.orchestration.workflow_planner_agent import WorkflowPlannerAgent

planner = WorkflowPlannerAgent()

# Plan workflow
workflow_def = planner.execute(
    input_data="Generate AP aging report",
    params={
        'report_type': 'ap_aging',
        'time_period': 'last_month',
        'include_details': True
    }
)

print(f"Workflow Steps: {len(workflow_def['workflow']['steps'])}")
print(f"Workflow Edges: {len(workflow_def['workflow']['edges'])}")
```

**Workflow Structure**:
```python
{
    'workflow': {
        'steps': [
            {
                'id': 'node_1',
                'type': 'InvoiceFetchNode',
                'name': 'Fetch Invoices',
                'params': {'category': 'purchase', 'date_range': 'last_month'}
            },
            {
                'id': 'node_2', 
                'type': 'OutstandingCalculatorNode',
                'name': 'Calculate Outstanding',
                'params': {}
            }
        ],
        'edges': [
            {'source': 'node_1', 'target': 'node_2'}
        ]
    }
}
```

### Prompt Library (`prompt_library.py`)

**Purpose**: Manages template-based prompts for different report types and operations.

**Key Features**:
- **Template Management**: Organizes prompts by category and type
- **Variable Injection**: Supports dynamic variable substitution
- **Multi-Language Support**: Handles different language requirements
- **Version Control**: Manages prompt versions and updates

**Usage**:
```python
from intelligence_layer.prompts.prompt_library import PromptLibrary

library = PromptLibrary()

# Get prompt template
prompt = library.get_prompt('ap_aging_report')
print(f"Prompt Name: {prompt.name}")
print(f"Description: {prompt.description}")

# Inject variables
rendered = library.inject_variables('ap_aging_report', {
    'time_period': 'last_month',
    'currency': 'INR'
})
```

**Prompt Categories**:
- **AP Reports**: AP aging, invoice register, overdue analysis
- **AR Reports**: AR aging, customer register, DSO analysis
- **Analysis Reports**: Revenue trends, expense analysis
- **Compliance Reports**: Audit trails, reconciliation reports
- **Tax Reports**: GST calculations, tax summaries

## 🔄 Workflow Orchestration

### Orchestrator (`orchestrator.py`)

**Purpose**: Main workflow execution engine that coordinates multi-step operations.

**Key Features**:
- **Node Execution**: Executes workflow nodes in dependency order
- **Error Handling**: Manages errors and provides fallback mechanisms
- **Progress Tracking**: Tracks execution progress and provides status updates
- **Result Aggregation**: Combines results from multiple nodes

**Usage**:
```python
from intelligence_layer.orchestration.orchestrator import Orchestrator

orchestrator = Orchestrator()

# Execute workflow
result = orchestrator.execute_workflow({
    'steps': [
        {'type': 'InvoiceFetchNode', 'params': {'category': 'purchase'}},
        {'type': 'OutstandingCalculatorNode', 'params': {}},
        {'type': 'AgingCalculatorNode', 'params': {'as_of_date': '2024-12-31'}}
    ],
    'edges': [
        {'source': '0', 'target': '1'},
        {'source': '1', 'target': '2'}
    ]
})

print(f"Execution Status: {result['status']}")
print(f"Execution Time: {result['execution_time_ms']}ms")
```

### Enhanced Orchestrator (`enhanced_orchestrator.py`)

**Purpose**: Advanced workflow engine with additional features for complex operations.

**Enhanced Features**:
- **Parallel Execution**: Executes independent nodes in parallel
- **Conditional Logic**: Supports conditional node execution
- **Loop Support**: Handles iterative processing
- **State Management**: Maintains execution state across steps
- **Caching**: Caches intermediate results for performance

## 🧪 Testing and Validation

### Unit Tests
```python
import pytest
from intelligence_layer.routing.router_prompt_integrator import RouterPromptIntegrator

def test_query_processing():
    integrator = RouterPromptIntegrator()
    
    result = integrator.process_query("Show me AP aging for last month")
    
    assert result['status'] == 'success'
    assert result['domain'] == 'APLayer'
    assert 'ap_aging_report' in result['prompt_id']

def test_domain_classification():
    from intelligence_layer.parsing.domain_classifier import DomainClassifier
    
    classifier = DomainClassifier()
    result = classifier.classify("Generate revenue trend analysis")
    
    assert result['domain'] == 'AnalysisLayer'
    assert result['confidence'] > 0.8
```

### Integration Tests
```python
def test_complete_workflow():
    # Test complete query processing pipeline
    integrator = RouterPromptIntegrator()
    
    # Process query
    result = integrator.process_query(
        "Show me AP aging for last month with details",
        context={'user_id': 'test-user', 'company_id': 'test-company'}
    )
    
    # Execute workflow
    workflow_result = integrator.generate_report_from_query(
        "Show me AP aging for last month with details",
        context={'user_id': 'test-user', 'company_id': 'test-company'},
        execute=True
    )
    
    assert workflow_result['status'] == 'success'
    assert 'report_output' in workflow_result
```

## 📊 Performance Considerations

### Caching Strategy
- **Prompt Caching**: Cache rendered prompts to avoid re-processing
- **Classification Caching**: Cache domain classification results
- **Workflow Caching**: Cache frequently used workflow definitions

### Parallel Processing
- **Independent Nodes**: Execute nodes without dependencies in parallel
- **Async Operations**: Use async/await for I/O operations
- **Batch Processing**: Process multiple queries in batches

### Memory Management
- **Prompt Templates**: Load only required prompt templates
- **Variable Substitution**: Efficient string replacement algorithms
- **Result Streaming**: Stream large results to avoid memory issues

## 🔧 Configuration

### Environment Variables
```bash
# LLM Configuration
GROQ_API_KEY=your_groq_api_key
GOOGLE_API_KEY=your_google_api_key
OPENAI_API_KEY=your_openai_api_key

# Processing Configuration
MAX_WORKFLOW_STEPS=50
WORKFLOW_TIMEOUT=300
PARALLEL_NODE_LIMIT=10
```

### Prompt Configuration
```python
# Configure prompt library
from intelligence_layer.prompts.prompt_library import PromptLibrary

library = PromptLibrary()
library.load_prompts_from_directory('./prompts/')
library.set_default_language('en')
library.enable_caching(True)
```

## 🔒 Security

### Input Validation
- **Query Sanitization**: Sanitize user inputs to prevent injection attacks
- **Variable Validation**: Validate extracted variables
- **Prompt Security**: Ensure prompts don't contain malicious content

### Access Control
- **Domain Restrictions**: Restrict access to certain domains based on user roles
- **Query Limits**: Limit query complexity and execution time
- **Audit Logging**: Log all query processing for security analysis

---

**Next Layer**: [Processing Layer](../processing_layer/README.md) - Document processing and agent execution