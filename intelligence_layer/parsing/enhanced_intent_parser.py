"""
Enhanced Intent Parser Agent
Combines domain classification and variable extraction
Replaces the existing intent_parser_agent.py with enhanced functionality
"""

from typing import Dict, Any, Optional
import json
from datetime import datetime


class EnhancedIntentParser:
    """
    Enhanced Intent Parser
    
    Performs three-stage processing:
    1. Domain Classification (11 domains)
    2. Variable Extraction (time, entities, filters, output, analysis)
    3. Intent Structuring (combine into actionable intent)
    
    Input: "Show me AWS invoices from last month older than 60 days in Excel"
    
    Output: {
        "domain": "APLayer",
        "confidence": 0.95,
        "variables": {
            "time": {"date_from": "2025-12-01", "date_to": "2025-12-31"},
            "entities": {"vendor": "AWS"},
            "filters": {"aging_days": 60},
            "output": {"output_format": "excel"}
        },
        "report_type": "ap_aging",
        "action": "generate_report"
    }
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize enhanced intent parser
        
        Args:
            llm_client: LLM client (Groq/OpenAI)
        """
        self.llm = llm_client
        
        if self.llm is None:
            try:
                from shared.llm.groq_client import get_groq_client
                self.llm = get_groq_client("accurate")
            except:
                pass
        
        from intelligence_layer.parsing.domain_classifier import DomainClassifier
        from intelligence_layer.parsing.variable_extractor import VariableExtractor
        
        self.domain_classifier = DomainClassifier(llm_client=self.llm)
        self.variable_extractor = VariableExtractor(llm_client=self.llm)
    
    def parse(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Parse user query into structured intent
        
        Args:
            query: Natural language query
            context: Additional context (user_id, org_id, etc.)
            
        Returns:
            Complete intent with domain, variables, and action
        """
        context = context or {}
        
        print(f"\n{'='*70}")
        print(f"PARSING QUERY: {query}")
        print(f"{'='*70}\n")
        
        domain_result = self.domain_classifier.classify(query)
        print(f"Domain: {domain_result['domain']} (confidence: {domain_result['confidence']:.2f})")
        
        variables = self.variable_extractor.extract(query)
        print(f"Variables extracted: {len(variables)} categories")
        
        report_type = self._infer_report_type(domain_result['domain'], variables, query)
        print(f"Report Type: {report_type}")
        
        action = self._infer_action(domain_result['domain'], query)
        print(f"Action: {action}")
        
        intent = {
            'status': 'success',
            'domain': domain_result['domain'],
            'confidence': domain_result['confidence'],
            'reasoning': domain_result.get('reasoning', ''),
            'variables': variables,
            'report_type': report_type,
            'action': action,
            'query': query,
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"\n{'='*70}")
        print(f"INTENT PARSED SUCCESSFULLY")
        print(f"{'='*70}\n")
        
        return intent
    
    def _infer_report_type(self, domain: str, variables: Dict, query: str) -> str:
        """
        Infer specific report type based on domain and variables
        
        Args:
            domain: Classified domain
            variables: Extracted variables
            query: Original query
            
        Returns:
            Specific report type
        """
        query_lower = query.lower()
        
        if domain == "APLayer":
            if "aging" in query_lower:
                return "ap_aging"
            elif "overdue" in query_lower or "sla" in query_lower:
                return "ap_overdue"
            elif "duplicate" in query_lower:
                return "ap_duplicate"
            elif "register" in query_lower or "list" in query_lower:
                return "ap_register"
            else:
                return "ap_register"
        
        elif domain == "ARLayer":
            if "aging" in query_lower:
                return "ar_aging"
            elif "collection" in query_lower or "priority" in query_lower:
                return "ar_collection"
            elif "dso" in query_lower:
                return "dso"
            elif "register" in query_lower or "list" in query_lower:
                return "ar_register"
            else:
                return "ar_register"
        
        elif domain == "AnalysisLayer":
            if "trend" in query_lower:
                return "trend_analysis"
            elif "anomaly" in query_lower or "detect" in query_lower:
                return "anomaly_detection"
            elif "predict" in query_lower or "forecast" in query_lower:
                return "prediction"
            else:
                return "general_analysis"
        
        elif domain == "ReconciliationLayer":
            return "bank_reconciliation"
        
        elif domain == "ComplianceLayer":
            return "audit_report"
        
        elif domain == "CashFlowLayer":
            return "cash_flow_forecast"
        
        elif domain == "TaxLayer":
            if "gst" in query_lower:
                return "gst_report"
            elif "tds" in query_lower:
                return "tds_report"
            else:
                return "tax_report"
        
        elif domain == "BudgetLayer":
            if "variance" in query_lower:
                return "variance_analysis"
            else:
                return "budget_report"
        
        elif domain == "AlertLayer":
            return "alert_report"
        
        elif domain == "ReportLayer":
            return "custom_report"
        
        elif domain == "FinanceLayer":
            return "financial_summary"
        
        return "general_report"
    
    def _infer_action(self, domain: str, query: str) -> str:
        """
        Infer action to take based on domain and query
        
        Args:
            domain: Classified domain
            query: Original query
            
        Returns:
            Action type
        """
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['generate', 'create', 'produce', 'make']):
            return "generate_report"
        
        elif any(word in query_lower for word in ['show', 'display', 'list', 'view']):
            return "query_data"
        
        elif any(word in query_lower for word in ['analyze', 'analysis', 'examine']):
            return "analyze_data"
        
        elif any(word in query_lower for word in ['reconcile', 'match', 'compare']):
            return "reconcile_data"
        
        elif any(word in query_lower for word in ['forecast', 'predict', 'project']):
            return "forecast_data"
        
        elif any(word in query_lower for word in ['alert', 'notify', 'remind']):
            return "generate_alerts"
        
        else:
            return "generate_report"
    
    def get_execution_params(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert intent into execution parameters for agents
        
        Args:
            intent: Parsed intent
            
        Returns:
            Parameters ready for agent execution
        """
        params = {
            'domain': intent['domain'],
            'report_type': intent['report_type'],
            'action': intent['action']
        }
        
        variables = intent.get('variables', {})
        
        if 'time' in variables:
            params.update(variables['time'])
        
        if 'entities' in variables:
            params.update(variables['entities'])
        
        if 'filters' in variables:
            params.update(variables['filters'])
        
        if 'output' in variables:
            params.update(variables['output'])
        
        if 'analysis' in variables:
            params.update(variables['analysis'])
        
        if 'context' in intent:
            params.update(intent['context'])
        
        return params
    
    def format_for_display(self, intent: Dict[str, Any]) -> str:
        """
        Format intent for human-readable display
        
        Args:
            intent: Parsed intent
            
        Returns:
            Formatted string
        """
        lines = [
            f"Domain: {intent['domain']}",
            f"Confidence: {intent['confidence']:.2%}",
            f"Report Type: {intent['report_type']}",
            f"Action: {intent['action']}",
            ""
        ]
        
        variables = intent.get('variables', {})
        
        if variables.get('time'):
            lines.append("Time Parameters:")
            for key, value in variables['time'].items():
                lines.append(f"  - {key}: {value}")
            lines.append("")
        
        if variables.get('entities'):
            lines.append("Entities:")
            for key, value in variables['entities'].items():
                lines.append(f"  - {key}: {value}")
            lines.append("")
        
        if variables.get('filters'):
            lines.append("Filters:")
            for key, value in variables['filters'].items():
                lines.append(f"  - {key}: {value}")
            lines.append("")
        
        if variables.get('output'):
            lines.append("Output Settings:")
            for key, value in variables['output'].items():
                lines.append(f"  - {key}: {value}")
            lines.append("")
        
        return "\n".join(lines)


def test_enhanced_parser():
    """Test the enhanced intent parser"""
    
    parser = EnhancedIntentParser()
    
    test_queries = [
        "Show me AWS invoices from last month older than 60 days in Excel",
        "Analyze revenue trends for Q4 year over year",
        "Generate AP aging report for unpaid invoices over $10,000",
        "Reconcile bank statement for December",
        "Cash flow forecast for next quarter with charts",
        "Show overdue customer invoices",
        "Calculate GST for last month",
        "Budget vs actual variance analysis for Engineering department"
    ]
    
    print("=" * 70)
    print("ENHANCED INTENT PARSER TEST")
    print("=" * 70)
    
    for query in test_queries:
        intent = parser.parse(query)
        
        print(f"\n{parser.format_for_display(intent)}")
        
        params = parser.get_execution_params(intent)
        print("Execution Parameters:")
        print(json.dumps(params, indent=2))
        print("\n" + "=" * 70)


if __name__ == "__main__":
    test_enhanced_parser()