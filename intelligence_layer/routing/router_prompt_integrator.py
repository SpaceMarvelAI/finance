"""
Router-Prompt Integration
Connects LLM Router with Prompt Library for seamless report generation
"""

from typing import Dict, Any, Optional, List
import json
from datetime import datetime

from intelligence_layer.prompts.prompt_library import PromptLibrary, PromptCategory

try:
    from intelligence_layer.parsing.domain_classifier import DomainClassifier
    from intelligence_layer.parsing.variable_extractor import VariableExtractor
except ImportError:
    print("Error: Could not import router components")
    print("Make sure domain_classifier.py and variable_extractor.py are in the same directory")
    import sys
    sys.exit(1)

# Setup logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RouterPromptIntegrator:
    """
    Integration layer between Router and Prompt Library
    
    Flow:
    1. User query → Domain Classifier → Domain
    2. User query → Variable Extractor → Variables
    3. Domain + Variables → Prompt Library → Rendered Prompt
    4. Rendered Prompt → Agent → Report
    """
    
    def __init__(self):
        self.classifier = DomainClassifier()
        self.extractor = VariableExtractor()
        self.library = PromptLibrary()
        self.logger = logger
        
        # Map domains to agents
        self.domain_to_agent = {
            "FinanceLayer": "FinancialDashboardAgent",
            "APLayer": "APAgent",
            "ARLayer": "ARAgent",
            "ReportLayer": "ReportGeneratorAgent",
            "AnalysisLayer": "AnalysisAgent",
            "ReconciliationLayer": "ReconciliationAgent",
            "ComplianceLayer": "ComplianceAgent",
            "CashFlowLayer": "CashFlowAgent",
            "TaxLayer": "TaxAgent",
            "BudgetLayer": "BudgetAgent",
            "AlertLayer": "AlertAgent"
        }
        
        # Map domains to prompt IDs
        self.domain_to_prompts = self._build_domain_prompt_mapping()
    
    def _build_domain_prompt_mapping(self) -> Dict[str, List[str]]:
        """Map domains to available prompt IDs"""
        return {
            "APLayer": [
                "ap_aging_report",
                "ap_invoice_register",
                "ap_overdue_sla"
            ],
            "ARLayer": [
                "ar_aging_report",
                "ar_invoice_register"
            ],
            "AnalysisLayer": [
                "revenue_trend_analysis",
                "expense_analysis"
            ],
            "ReconciliationLayer": [
                "bank_reconciliation"
            ],
            "CashFlowLayer": [
                "cash_flow_forecast"
            ],
            "TaxLayer": [
                "gst_calculation"
            ],
            "BudgetLayer": [
                "budget_variance_analysis"
            ],
            "ComplianceLayer": [
                "audit_trail_report"
            ],
            "AlertLayer": [
                "overdue_alerts"
            ],
            "FinanceLayer": [
                "financial_dashboard"
            ],
            "ReportLayer": [
                "financial_dashboard",
                "ap_aging_report",
                "ar_aging_report"
            ]
        }
    
    def process_query(
        self, 
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process natural language query into report configuration
        
        Args:
            query: Natural language query
            context: Optional context (user_id, org_id, etc.)
            
        Returns:
            {
                'domain': str,
                'agent': str,
                'prompt_id': str,
                'rendered_prompt': str,
                'variables': dict,
                'report_config': dict,
                'confidence': float
            }
        """
        context = context or {}
        
        self.logger.info(f"Processing query: {query}")
        
        # STEP 1: Classify domain
        classification = self.classifier.classify(query)
        domain = classification['domain']
        confidence = classification['confidence']
        agent = self.domain_to_agent.get(domain, "UnknownAgent")
        
        self.logger.info(f"Classified as: {domain} ({confidence:.2%})")
        
        # STEP 2: Extract variables
        extraction = self.extractor.extract(query)
        
        # Restructure extraction result into variables dict
        variables = {
            'time': extraction.get('time', {}),
            'entities': extraction.get('entities', {}),
            'filters': extraction.get('filters', {}),
            'output': extraction.get('output', {}),
            'analysis': extraction.get('analysis', {})
        }
        
        self.logger.info(f"Extracted variables: {json.dumps(variables, indent=2)}")
        
        # STEP 3: Select appropriate prompt
        prompt_id = self._select_prompt(domain, query, variables)
        
        if not prompt_id:
            return {
                'status': 'error',
                'error': f'No prompt found for domain: {domain}',
                'domain': domain,
                'variables': variables
            }
        
        self.logger.info(f"Selected prompt: {prompt_id}")
        
        # STEP 4: Render prompt with variables
        rendered_prompt = self.library.inject_variables(prompt_id, variables)
        
        # STEP 5: Build report configuration
        prompt_template = self.library.get_prompt(prompt_id)
        
        report_config = {
            'report_type': prompt_template.report_type,
            'domain': domain,
            'agent': agent,
            'prompt': rendered_prompt,
            'variables': variables,
            'output_format': variables.get('output', {}).get('output_format', 'excel'),
            'timestamp': datetime.now().isoformat(),
            'user_query': query
        }
        
        return {
            'status': 'success',
            'domain': domain,
            'agent': agent,
            'prompt_id': prompt_id,
            'rendered_prompt': rendered_prompt,
            'variables': variables,
            'report_config': report_config,
            'confidence': confidence,
            'execution_time': classification.get('execution_time', 0)
        }
    
    def _select_prompt(
        self, 
        domain: str, 
        query: str, 
        variables: Dict[str, Any]
    ) -> Optional[str]:
        """
        Select the most appropriate prompt for the query
        
        Uses heuristics based on:
        - Domain classification
        - Keywords in query
        - Extracted variables
        """
        available_prompts = self.domain_to_prompts.get(domain, [])
        
        if not available_prompts:
            return None
        
        # If only one prompt available, use it
        if len(available_prompts) == 1:
            return available_prompts[0]
        
        # Use keywords to select best prompt
        query_lower = query.lower()
        
        # AP Layer selection
        if domain == "APLayer":
            if any(word in query_lower for word in ['aging', 'bucket', 'overdue days']):
                return "ap_aging_report"
            elif any(word in query_lower for word in ['overdue', 'sla', 'late', 'past due']):
                return "ap_overdue_sla"
            else:
                return "ap_invoice_register"
        
        # AR Layer selection
        elif domain == "ARLayer":
            if any(word in query_lower for word in ['aging', 'bucket', 'dso']):
                return "ar_aging_report"
            else:
                return "ar_invoice_register"
        
        # Analysis Layer selection
        elif domain == "AnalysisLayer":
            if any(word in query_lower for word in ['revenue', 'sales', 'income']):
                return "revenue_trend_analysis"
            else:
                return "expense_analysis"
        
        # Default to first available prompt
        return available_prompts[0]
    
    def generate_report_from_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        execute: bool = False
    ) -> Dict[str, Any]:
        """
        Complete pipeline: Query → Prompt → Report
        
        Args:
            query: Natural language query
            context: Optional context
            execute: Whether to execute the report generation
            
        Returns:
            Complete report configuration or executed report
        """
        # Process query
        result = self.process_query(query, context)
        
        if result['status'] == 'error':
            return result
        
        # If not executing, return configuration
        if not execute:
            return result
        
        # Execute report generation (integrate with orchestrator)
        from intelligence_layer.orchestration.orchestrator import Orchestrator
        
        orchestrator = Orchestrator()
        report_result = orchestrator.generate_report(
            report_type=result['report_config']['report_type'],
            params=result['variables'],
            context=context
        )
        
        return {
            **result,
            'report_output': report_result
        }
    
    def get_available_prompts_for_domain(self, domain: str) -> List[Dict[str, Any]]:
        """Get all available prompts for a domain"""
        prompt_ids = self.domain_to_prompts.get(domain, [])
        
        prompts = []
        for prompt_id in prompt_ids:
            prompt = self.library.get_prompt(prompt_id)
            if prompt:
                prompts.append({
                    'id': prompt.id,
                    'name': prompt.name,
                    'description': prompt.description,
                    'examples': prompt.examples
                })
        
        return prompts
    
    def suggest_queries(self, domain: Optional[str] = None) -> List[str]:
        """
        Suggest example queries
        
        Args:
            domain: Optional domain filter
            
        Returns:
            List of example queries
        """
        if domain:
            prompt_ids = self.domain_to_prompts.get(domain, [])
        else:
            prompt_ids = [p.id for p in self.library.prompts.values()]
        
        examples = []
        for prompt_id in prompt_ids:
            prompt = self.library.get_prompt(prompt_id)
            if prompt:
                examples.extend(prompt.examples)
        
        return examples


# ===== EXAMPLE USAGE =====

def demo():
    """Demonstrate the integration"""
    integrator = RouterPromptIntegrator()
    
    # Example queries
    queries = [
        "Show me AP aging for last month",
        "Generate revenue trend analysis for Q4 year over year",
        "List all AWS invoices from December over $5000",
        "Calculate GST for last quarter",
        "Budget vs actual variance for Engineering department",
        "Cash flow forecast for next 90 days",
        "Reconcile bank statement for December 2024"
    ]
    
    print("="*80)
    print("ROUTER-PROMPT INTEGRATION DEMO")
    print("="*80)
    
    for query in queries:
        print(f"\nQuery: {query}")
        print("-"*80)
        
        result = integrator.process_query(query)
        
        if result['status'] == 'success':
            print(f"✓ Domain: {result['domain']}")
            print(f"✓ Agent: {result['agent']}")
            print(f"✓ Prompt: {result['prompt_id']}")
            print(f"✓ Confidence: {result['confidence']:.2%}")
            print(f"\nExtracted Variables:")
            for category, values in result['variables'].items():
                if values:
                    print(f"  {category}: {values}")
            
            print(f"\n📄 Rendered Prompt Preview (first 300 chars):")
            print(result['rendered_prompt'][:300] + "...")
        else:
            print(f"✗ Error: {result['error']}")
        
        print()
    
    # Show suggested queries
    print("\n" + "="*80)
    print("SUGGESTED QUERIES BY DOMAIN")
    print("="*80)
    
    for domain in ["APLayer", "ARLayer", "AnalysisLayer", "TaxLayer"]:
        examples = integrator.suggest_queries(domain)
        print(f"\n{domain}:")
        for example in examples[:2]:  # Show first 2
            print(f"  • {example}")


if __name__ == "__main__":
    demo()