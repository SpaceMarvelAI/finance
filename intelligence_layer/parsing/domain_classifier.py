"""
Domain Classifier
Classifies user queries into 11 financial domains using LLM
"""

from typing import Dict, Any, Optional
from enum import Enum
import json
import re
from datetime import datetime


class FinancialDomain(Enum):
    """11 Financial Domain Categories"""
    FINANCE_LAYER = "FinanceLayer"
    AP_LAYER = "APLayer"
    AR_LAYER = "ARLayer"
    REPORT_LAYER = "ReportLayer"
    ANALYSIS_LAYER = "AnalysisLayer"
    RECONCILIATION_LAYER = "ReconciliationLayer"
    COMPLIANCE_LAYER = "ComplianceLayer"
    CASH_FLOW_LAYER = "CashFlowLayer"
    TAX_LAYER = "TaxLayer"
    BUDGET_LAYER = "BudgetLayer"
    ALERT_LAYER = "AlertLayer"


class DomainClassifier:
    """
    Domain Classifier using LLM
    
    Classifies queries into one of 11 financial domains
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize domain classifier
        
        Args:
            llm_client: LLM client for classification
        """
        self.llm = llm_client
        
        if self.llm is None:
            try:
                from shared.llm.groq_client import get_groq_client
                self.llm = get_groq_client("accurate")
            except ImportError:
                try:
                    from groq_client import get_groq_client
                    self.llm = get_groq_client("accurate")
                except ImportError:
                    print("Warning: Could not import LLM client, using keyword fallback")
                    self.llm = None
    
    def classify(self, query: str) -> Dict[str, Any]:
        """
        Classify query into domain
        
        Args:
            query: User query string
            
        Returns:
            {
                "domain": "APLayer",
                "confidence": 0.95,
                "reasoning": "Query asks for vendor invoices",
                "fallback_used": False
            }
        """
        
        if self.llm:
            try:
                return self._classify_with_llm(query)
            except Exception as e:
                print(f"LLM classification failed: {e}, using fallback")
        
        return self._classify_with_keywords(query)
    
    def _classify_with_llm(self, query: str) -> Dict[str, Any]:
        """
        Classify using LLM
        
        Args:
            query: User query
            
        Returns:
            Classification result
        """
        prompt = self._build_classification_prompt(query)
        
        response = self.llm.generate(prompt)
        
        result = self._extract_json_from_response(response)
        result['fallback_used'] = False
        
        return result
    
    def _build_classification_prompt(self, query: str) -> str:
        """Build LLM prompt for domain classification"""
        
        return f"""
Classify this financial query into ONE of these 11 domains.

IMPORTANT: Consider CONTEXT when classifying. Compound terms like "AP SLA" or "AR aging" should be classified based on the PRIMARY domain context, not individual keywords.

DOMAINS:
1. FinanceLayer - General financial queries, KPIs, metrics, financial summary
   Examples: "What's our revenue?", "Show financial dashboard", "Total expenses"

2. APLayer - Accounts Payable operations, vendor invoices, purchase orders
   Examples: "Show AP aging", "Vendor invoices", "AWS bills", "AP SLA overdue", "AP payment terms"
   KEYWORDS: ap, accounts payable, vendor, purchase, payable, supplier, bill, expense
   CONTEXT RULES: 
   - "AP SLA" = APLayer (Accounts Payable SLA)
   - "AP aging" = APLayer (Accounts Payable aging)
   - "AP overdue" = APLayer (Accounts Payable overdue)

3. ARLayer - Accounts Receivable operations, customer invoices, sales
   Examples: "Customer invoices", "AR aging", "Outstanding receivables", "AR SLA violations"
   KEYWORDS: ar, accounts receivable, customer, sales, receivable, collection, payment received
   CONTEXT RULES:
   - "AR aging" = ARLayer (Accounts Receivable aging)
   - "AR SLA" = ARLayer (Accounts Receivable SLA)

4. ReportLayer - Custom report generation, scheduled reports
   Examples: "Generate monthly report", "Create quarterly summary"

5. AnalysisLayer - Deep analysis, trends, predictions, anomaly detection
   Examples: "Analyze revenue trends", "Detect anomalies", "Predict churn"

6. ReconciliationLayer - Bank reconciliation, payment matching
   Examples: "Reconcile bank statement", "Match payments", "Find unmatched"

7. ComplianceLayer - Audit trails, compliance checks, regulatory reports
   Examples: "Audit report", "Compliance check", "SOX requirements"

8. CashFlowLayer - Cash flow management, forecasting, working capital
   Examples: "Cash flow forecast", "Working capital analysis"

9. TaxLayer - Tax calculations, GST/VAT, tax returns
   Examples: "Calculate GST", "Tax liability", "TDS report"

10. BudgetLayer - Budget planning, variance analysis, forecasting
    Examples: "Budget vs actual", "Variance analysis", "Budget forecast"

11. AlertLayer - Alerts, notifications, overdue items (GENERAL alerts, not AP/AR specific)
    Examples: "Show overdue invoices", "Payment reminders", "SLA breaches", "System alerts"
    KEYWORDS: alert, reminder, notification, breach, warning, urgent
    CONTEXT RULES:
    - "SLA breaches" = AlertLayer (when not AP/AR context)
    - "Overdue items" = AlertLayer (when not AP/AR context)
    - "System alerts" = AlertLayer

Query: "{query}"

CRITICAL CLASSIFICATION RULES:
1. If query contains "AP" + financial term → APLayer
2. If query contains "AR" + financial term → ARLayer  
3. If query contains "SLA" without AP/AR context → AlertLayer
4. If query contains "overdue" without AP/AR context → AlertLayer
5. Compound terms take precedence over individual keywords

Examples:
- "AP SLA overdue" → APLayer (not AlertLayer)
- "AR aging report" → ARLayer
- "SLA violations" → AlertLayer (no AP/AR context)
- "Overdue customer payments" → ARLayer (customer context)
- "Overdue vendor payments" → APLayer (vendor context)

Analyze the query and determine which domain it belongs to.

Respond with ONLY this JSON:
{{
    "domain": "DomainName",
    "confidence": 0.95,
    "reasoning": "Brief explanation of why this domain was chosen, including context analysis"
}}

Be precise. Choose the MOST specific domain that matches the query.
"""
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response"""
        
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(0)
            result = json.loads(json_str)
            
            if 'domain' in result:
                return result
        
        raise ValueError("No valid JSON found in LLM response")
    
    def _classify_with_keywords(self, query: str) -> Dict[str, Any]:
        """
        Fallback keyword-based classification
        
        Args:
            query: User query
            
        Returns:
            Classification result
        """
        query_lower = query.lower()
        
        domain_keywords = {
            FinancialDomain.AP_LAYER: [
                'ap', 'accounts payable', 'vendor', 'purchase', 'payable',
                'supplier', 'bill', 'aws', 'google cloud', 'expense'
            ],
            FinancialDomain.AR_LAYER: [
                'ar', 'accounts receivable', 'customer', 'sales', 'receivable',
                'invoice', 'collection', 'payment received'
            ],
            FinancialDomain.ANALYSIS_LAYER: [
                'analyze', 'analysis', 'trend', 'predict', 'forecast',
                'anomaly', 'detect', 'pattern', 'insight', 'churn'
            ],
            FinancialDomain.REPORT_LAYER: [
                'report', 'generate report', 'create report', 'summary',
                'dashboard', 'export', 'download'
            ],
            FinancialDomain.RECONCILIATION_LAYER: [
                'reconcile', 'reconciliation', 'match', 'matching',
                'bank statement', 'unmatched', 'mismatch'
            ],
            FinancialDomain.COMPLIANCE_LAYER: [
                'audit', 'compliance', 'regulatory', 'sox', 'internal control',
                'audit trail', 'governance'
            ],
            FinancialDomain.CASH_FLOW_LAYER: [
                'cash flow', 'working capital', 'liquidity', 'cash position',
                'cash forecast', 'cash management'
            ],
            FinancialDomain.TAX_LAYER: [
                'tax', 'gst', 'vat', 'tds', 'tax liability', 'tax return',
                'withholding tax', 'sales tax'
            ],
            FinancialDomain.BUDGET_LAYER: [
                'budget', 'variance', 'budget vs actual', 'forecast',
                'planning', 'budgeting', 'allocation'
            ],
            FinancialDomain.ALERT_LAYER: [
                'alert', 'overdue', 'reminder', 'notification', 'sla',
                'breach', 'warning', 'urgent'
            ],
            FinancialDomain.FINANCE_LAYER: [
                'revenue', 'profit', 'loss', 'kpi', 'metric',
                'financial summary', 'performance', 'total'
            ]
        }
        
        domain_scores = {}
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                domain_scores[domain] = score
        
        if domain_scores:
            best_domain = max(domain_scores, key=domain_scores.get)
            max_score = domain_scores[best_domain]
            confidence = min(0.7, 0.5 + (max_score * 0.1))
            
            return {
                'domain': best_domain.value,
                'confidence': confidence,
                'reasoning': f'Keyword match (score: {max_score})',
                'fallback_used': True
            }
        
        return {
            'domain': FinancialDomain.FINANCE_LAYER.value,
            'confidence': 0.3,
            'reasoning': 'Default classification - no strong keyword matches',
            'fallback_used': True
        }
    
    def get_domain_metadata(self, domain: str) -> Dict[str, Any]:
        """
        Get metadata about a domain
        
        Args:
            domain: Domain name
            
        Returns:
            Domain metadata
        """
        metadata = {
            'FinanceLayer': {
                'description': 'General financial queries and KPIs',
                'typical_agents': ['FinancialSummaryAgent', 'KPIAgent'],
                'common_outputs': ['dashboard', 'summary', 'metrics']
            },
            'APLayer': {
                'description': 'Accounts Payable operations',
                'typical_agents': ['APAgingAgent', 'APRegisterAgent', 'VendorAgent'],
                'common_outputs': ['ap_aging', 'vendor_report', 'payment_schedule']
            },
            'ARLayer': {
                'description': 'Accounts Receivable operations',
                'typical_agents': ['ARAgingAgent', 'ARRegisterAgent', 'CollectionAgent'],
                'common_outputs': ['ar_aging', 'customer_report', 'collection_priority']
            },
            'ReportLayer': {
                'description': 'Custom report generation',
                'typical_agents': ['ReportGeneratorAgent', 'TemplateAgent'],
                'common_outputs': ['custom_report', 'scheduled_report']
            },
            'AnalysisLayer': {
                'description': 'Deep analysis and predictions',
                'typical_agents': ['TrendAnalysisAgent', 'AnomalyDetectionAgent'],
                'common_outputs': ['analysis_report', 'predictions', 'insights']
            },
            'ReconciliationLayer': {
                'description': 'Reconciliation and matching',
                'typical_agents': ['BankReconciliationAgent', 'PaymentMatchingAgent'],
                'common_outputs': ['reconciliation_report', 'matched_items']
            },
            'ComplianceLayer': {
                'description': 'Audit and compliance',
                'typical_agents': ['AuditTrailAgent', 'ComplianceCheckAgent'],
                'common_outputs': ['audit_report', 'compliance_status']
            },
            'CashFlowLayer': {
                'description': 'Cash flow management',
                'typical_agents': ['CashFlowAgent', 'LiquidityAgent'],
                'common_outputs': ['cash_flow_forecast', 'liquidity_report']
            },
            'TaxLayer': {
                'description': 'Tax calculations and returns',
                'typical_agents': ['TaxCalculationAgent', 'GSTAgent', 'TDSAgent'],
                'common_outputs': ['tax_report', 'gst_return', 'tds_summary']
            },
            'BudgetLayer': {
                'description': 'Budget planning and variance',
                'typical_agents': ['BudgetAgent', 'VarianceAgent', 'ForecastAgent'],
                'common_outputs': ['budget_report', 'variance_analysis']
            },
            'AlertLayer': {
                'description': 'Alerts and notifications',
                'typical_agents': ['AlertAgent', 'ReminderAgent', 'SLAAgent'],
                'common_outputs': ['alert_list', 'overdue_items', 'notifications']
            }
        }
        
        return metadata.get(domain, {})


def test_domain_classifier():
    """Test the domain classifier"""
    
    classifier = DomainClassifier()
    
    test_queries = [
        "Show me AWS invoices from last month",
        "Analyze revenue trends for Q4",
        "Reconcile bank statement",
        "Generate AP aging report",
        "Show overdue customer invoices",
        "Calculate GST for December",
        "Budget vs actual variance",
        "Cash flow forecast for next quarter",
        "Audit trail for vendor payments",
        "What's our total revenue?"
    ]
    
    print("=" * 70)
    print("DOMAIN CLASSIFIER TEST")
    print("=" * 70)
    
    for query in test_queries:
        result = classifier.classify(query)
        print(f"\nQuery: {query}")
        print(f"Domain: {result['domain']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Reasoning: {result['reasoning']}")
        print(f"Fallback: {result['fallback_used']}")


if __name__ == "__main__":
    test_domain_classifier()