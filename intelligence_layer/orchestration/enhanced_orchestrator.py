"""
Enhanced Master Orchestrator
Uses 11-domain classification and variable extraction for intelligent routing
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json


class EnhancedOrchestrator:
    """
    Enhanced Master Orchestrator
    
    Features:
    1. 11-domain classification
    2. Variable extraction from queries
    3. Domain-based agent routing
    4. Execution with extracted parameters
    5. Result aggregation
    
    Architecture:
    Query → Parse (Domain + Variables) → Route → Execute → Return
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize orchestrator
        
        Args:
            llm_client: LLM client for parsing
        """
        from intelligence_layer.parsing.enhanced_intent_parser import EnhancedIntentParser
        
        self.parser = EnhancedIntentParser(llm_client=llm_client)
        self.execution_history = []
        
        self.domain_agent_map = self._build_domain_agent_map()
    
    def execute(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute complete workflow from query to result
        
        Args:
            query: Natural language query
            context: Additional context (user_id, org_id, etc.)
            
        Returns:
            {
                "status": "success",
                "domain": "APLayer",
                "report_type": "ap_aging",
                "result": {...},
                "execution_time": 1.23
            }
        """
        start_time = datetime.now()
        
        print(f"\n{'='*70}")
        print(f"ORCHESTRATOR: Processing Query")
        print(f"{'='*70}")
        print(f"Query: {query}\n")
        
        try:
            intent = self.parser.parse(query, context)
            
            if intent.get('status') != 'success':
                return {
                    'status': 'error',
                    'error': 'Intent parsing failed',
                    'details': intent
                }
            
            print(f"Step 1: Intent Parsed")
            print(f"  Domain: {intent['domain']}")
            print(f"  Report Type: {intent['report_type']}")
            print(f"  Confidence: {intent['confidence']:.2%}\n")
            
            agent = self._select_agent(intent)
            
            if not agent:
                return {
                    'status': 'error',
                    'error': f"No agent available for domain: {intent['domain']}",
                    'intent': intent
                }
            
            print(f"Step 2: Agent Selected")
            print(f"  Agent: {agent['name']}\n")
            
            params = self.parser.get_execution_params(intent)
            
            print(f"Step 3: Executing Agent")
            print(f"  Parameters: {len(params)} variables\n")
            
            result = self._execute_agent(agent, params)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            print(f"Step 4: Execution Complete")
            print(f"  Time: {execution_time:.2f}s\n")
            
            self._log_execution(query, intent, result, execution_time)
            
            return {
                'status': 'success',
                'domain': intent['domain'],
                'report_type': intent['report_type'],
                'action': intent['action'],
                'result': result,
                'intent': intent,
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            print(f"ERROR: {str(e)}\n")
            
            return {
                'status': 'error',
                'error': str(e),
                'query': query,
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat()
            }
    
    def _select_agent(self, intent: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Select appropriate agent based on domain and report type
        
        Args:
            intent: Parsed intent
            
        Returns:
            Agent configuration or None
        """
        domain = intent['domain']
        report_type = intent['report_type']
        
        domain_agents = self.domain_agent_map.get(domain, [])
        
        for agent in domain_agents:
            if report_type in agent.get('supported_reports', []):
                return agent
        
        if domain_agents:
            return domain_agents[0]
        
        return None
    
    def _execute_agent(self, agent: Dict[str, Any], params: Dict[str, Any]) -> Any:
        """
        Execute selected agent with parameters
        
        Args:
            agent: Agent configuration
            params: Execution parameters
            
        Returns:
            Agent result
        """
        agent_name = agent['name']
        agent_class = agent.get('class')
        
        if agent_class:
            agent_instance = agent_class()
            return agent_instance.execute(params=params)
        
        return {
            'status': 'simulated',
            'message': f'Agent {agent_name} execution simulated',
            'parameters': params
        }
    
    def _build_domain_agent_map(self) -> Dict[str, list]:
        """
        Build mapping of domains to agents
        
        Returns:
            Domain → Agent mapping
        """
        domain_map = {
            'FinanceLayer': [
                {
                    'name': 'FinancialSummaryAgent',
                    'description': 'Generate financial summaries and KPIs',
                    'supported_reports': ['financial_summary', 'kpi_dashboard'],
                    'class': None
                },
                {
                    'name': 'MetricsAgent',
                    'description': 'Calculate financial metrics',
                    'supported_reports': ['metrics_report'],
                    'class': None
                }
            ],
            'APLayer': [
                {
                    'name': 'APAgingAgent',
                    'description': 'Generate AP aging reports',
                    'supported_reports': ['ap_aging'],
                    'class': None
                },
                {
                    'name': 'APRegisterAgent',
                    'description': 'Generate AP register/list',
                    'supported_reports': ['ap_register'],
                    'class': None
                },
                {
                    'name': 'APOverdueAgent',
                    'description': 'Track overdue payables',
                    'supported_reports': ['ap_overdue'],
                    'class': None
                },
                {
                    'name': 'APDuplicateAgent',
                    'description': 'Detect duplicate invoices',
                    'supported_reports': ['ap_duplicate'],
                    'class': None
                }
            ],
            'ARLayer': [
                {
                    'name': 'ARAgingAgent',
                    'description': 'Generate AR aging reports',
                    'supported_reports': ['ar_aging'],
                    'class': None
                },
                {
                    'name': 'ARRegisterAgent',
                    'description': 'Generate AR register/list',
                    'supported_reports': ['ar_register'],
                    'class': None
                },
                {
                    'name': 'CollectionAgent',
                    'description': 'Prioritize collections',
                    'supported_reports': ['ar_collection'],
                    'class': None
                },
                {
                    'name': 'DSOAgent',
                    'description': 'Calculate DSO metrics',
                    'supported_reports': ['dso'],
                    'class': None
                }
            ],
            'ReportLayer': [
                {
                    'name': 'ReportGeneratorAgent',
                    'description': 'Generate custom reports',
                    'supported_reports': ['custom_report', 'scheduled_report'],
                    'class': None
                }
            ],
            'AnalysisLayer': [
                {
                    'name': 'TrendAnalysisAgent',
                    'description': 'Analyze trends and patterns',
                    'supported_reports': ['trend_analysis'],
                    'class': None
                },
                {
                    'name': 'AnomalyDetectionAgent',
                    'description': 'Detect anomalies',
                    'supported_reports': ['anomaly_detection'],
                    'class': None
                },
                {
                    'name': 'PredictionAgent',
                    'description': 'Make predictions',
                    'supported_reports': ['prediction'],
                    'class': None
                }
            ],
            'ReconciliationLayer': [
                {
                    'name': 'BankReconciliationAgent',
                    'description': 'Reconcile bank statements',
                    'supported_reports': ['bank_reconciliation'],
                    'class': None
                },
                {
                    'name': 'PaymentMatchingAgent',
                    'description': 'Match payments to invoices',
                    'supported_reports': ['payment_matching'],
                    'class': None
                }
            ],
            'ComplianceLayer': [
                {
                    'name': 'AuditTrailAgent',
                    'description': 'Generate audit trails',
                    'supported_reports': ['audit_report', 'audit_trail'],
                    'class': None
                },
                {
                    'name': 'ComplianceCheckAgent',
                    'description': 'Check compliance',
                    'supported_reports': ['compliance_check'],
                    'class': None
                }
            ],
            'CashFlowLayer': [
                {
                    'name': 'CashFlowAgent',
                    'description': 'Forecast cash flow',
                    'supported_reports': ['cash_flow_forecast'],
                    'class': None
                },
                {
                    'name': 'LiquidityAgent',
                    'description': 'Analyze liquidity',
                    'supported_reports': ['liquidity_report'],
                    'class': None
                }
            ],
            'TaxLayer': [
                {
                    'name': 'TaxCalculationAgent',
                    'description': 'Calculate taxes',
                    'supported_reports': ['tax_report'],
                    'class': None
                },
                {
                    'name': 'GSTAgent',
                    'description': 'Process GST',
                    'supported_reports': ['gst_report'],
                    'class': None
                },
                {
                    'name': 'TDSAgent',
                    'description': 'Process TDS',
                    'supported_reports': ['tds_report'],
                    'class': None
                }
            ],
            'BudgetLayer': [
                {
                    'name': 'BudgetAgent',
                    'description': 'Manage budgets',
                    'supported_reports': ['budget_report'],
                    'class': None
                },
                {
                    'name': 'VarianceAgent',
                    'description': 'Analyze variances',
                    'supported_reports': ['variance_analysis'],
                    'class': None
                }
            ],
            'AlertLayer': [
                {
                    'name': 'AlertAgent',
                    'description': 'Generate alerts',
                    'supported_reports': ['alert_report'],
                    'class': None
                },
                {
                    'name': 'ReminderAgent',
                    'description': 'Send reminders',
                    'supported_reports': ['reminder'],
                    'class': None
                }
            ]
        }
        
        return domain_map
    
    def _log_execution(self, query: str, intent: Dict, result: Any, execution_time: float):
        """Log execution for history"""
        
        self.execution_history.append({
            'query': query,
            'domain': intent['domain'],
            'report_type': intent['report_type'],
            'confidence': intent['confidence'],
            'execution_time': execution_time,
            'timestamp': datetime.now().isoformat(),
            'status': result.get('status', 'unknown')
        })
    
    def get_execution_history(self) -> list:
        """Get execution history"""
        return self.execution_history
    
    def get_available_domains(self) -> Dict[str, Any]:
        """Get list of available domains"""
        
        return {
            domain: {
                'agents': [agent['name'] for agent in agents],
                'description': agents[0].get('description', '') if agents else ''
            }
            for domain, agents in self.domain_agent_map.items()
        }


def test_orchestrator():
    """Test the enhanced orchestrator"""
    
    orchestrator = EnhancedOrchestrator()
    
    test_queries = [
        "Show me AWS invoices from last month older than 60 days in Excel",
        "Analyze revenue trends for Q4",
        "Generate AP aging report for unpaid invoices",
        "Reconcile bank statement for December",
        "Show overdue customer invoices",
        "Calculate GST for last month",
        "Cash flow forecast for next quarter",
        "Budget vs actual variance analysis"
    ]
    
    print("=" * 70)
    print("ENHANCED ORCHESTRATOR TEST")
    print("=" * 70)
    
    for query in test_queries:
        result = orchestrator.execute(query)
        
        print(f"\nResult Status: {result['status']}")
        if result['status'] == 'success':
            print(f"Domain: {result['domain']}")
            print(f"Report Type: {result['report_type']}")
            print(f"Execution Time: {result['execution_time']:.2f}s")
        else:
            print(f"Error: {result.get('error')}")
        
        print("\n" + "=" * 70)


if __name__ == "__main__":
    test_orchestrator()