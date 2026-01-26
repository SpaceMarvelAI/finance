"""
Master Orchestrator Agent
Coordinates all specialized agents
"""

from typing import Dict, Any, Optional
from processing_layer.agents.core.base_agent import BaseAgent, register_agent
from intelligence_layer.parsing.intent_parser_agent import IntentParserAgent
from processing_layer.agents.core.universal_report_agent import UniversalReportAgent
from shared.config.config_manager import get_config_manager, get_workflow_builder
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


@register_agent
class MasterOrchestratorAgent(BaseAgent):
    """
    Master Orchestrator Agent
    
    Top-level coordinator for all workflows
    
    Responsibilities:
    1. Parse user intent
    2. Load appropriate configuration
    3. Select execution strategy (report vs workflow)
    4. Coordinate execution
    5. Handle errors
    """
    
    def __init__(self):
        """Initialize orchestrator"""
        super().__init__("MasterOrchestratorAgent")
        
        self.intent_parser = IntentParserAgent()
        self.config_mgr = get_config_manager()
        self.workflow_builder = get_workflow_builder()
    
    def execute(self, input_data: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute complete workflow from natural language
        
        Args:
            input_data: Natural language query
            params: Additional parameters (user_id, org_id, etc)
            
        Returns:
            {
                "status": "success|error",
                "report_type": "...",
                "result": {...},
                "execution_history": [...]
            }
        """
        query = input_data
        params = params or {}
        
        user_id = params.get('user_id', 'default')
        org_id = params.get('org_id', 'default')
        
        self.logger.info(f"Orchestrator received query: {query}")
        
        try:
            # STEP 1: Parse intent
            self._log_decision(
                "Step 1: Parse user intent",
                "Using Intent Parser Agent"
            )
            
            intent = self.intent_parser.execute(query, params)
            
            if intent.get('status') != 'success':
                return {
                    'status': 'error',
                    'error': 'Intent parsing failed',
                    'details': intent
                }
            
            report_type = intent.get('report_type')
            filters = intent.get('filters', {})
            output_format = intent.get('output_format', 'excel')
            
            self._log_decision(
                f"Intent parsed: {report_type}",
                f"Filters: {filters}, Format: {output_format}"
            )
            
            # STEP 2: Build workflow configuration
            self._log_decision(
                "Step 2: Build workflow configuration",
                f"Report: {report_type}, Org: {org_id}"
            )
            
            workflow_config = self.workflow_builder.build_workflow(intent, org_id)
            
            if not workflow_config:
                return {
                    'status': 'error',
                    'error': f'No configuration found for report type: {report_type}',
                    'intent': intent
                }
            
            # STEP 3: Execute workflow
            self._log_decision(
                "Step 3: Execute workflow",
                f"Pipeline steps: {len(workflow_config.get('pipeline', []))}"
            )
            
            # Create universal report agent
            agent = UniversalReportAgent(workflow_config)
            
            # Execute with merged parameters
            execution_params = {
                'user_id': user_id,
                'org_id': org_id,
                **filters,
                **params
            }
            
            result = agent.execute(params=execution_params)
            
            if result.get('status') != 'success':
                return {
                    'status': 'error',
                    'error': 'Workflow execution failed',
                    'details': result,
                    'orchestrator_history': self.get_execution_history()
                }
            
            # STEP 4: Return result with metadata
            self._log_decision(
                "Workflow completed successfully",
                f"Report: {report_type}"
            )
            
            return {
                'status': 'success',
                'report_type': report_type,
                'result': result.get('data'),
                'intent': intent,
                'orchestrator_history': self.get_execution_history(),
                'agent_history': result.get('execution_history', [])
            }
            
        except Exception as e:
            logger.error(f"Orchestration failed: {e}", exc_info=True)
            
            return {
                'status': 'error',
                'error': str(e),
                'query': query,
                'orchestrator_history': self.get_execution_history()
            }
    
    def get_available_reports(self) -> Dict[str, str]:
        """
        Get list of available report types
        
        Returns:
            Dict of report_type: description
        """
        return {
            "ap_register": "AP Invoice Register - List of all purchase invoices",
            "ap_aging": "AP Aging Report - Aging analysis of payables",
            "ap_overdue": "AP Overdue & SLA - Overdue invoices with SLA breaches",
            "ap_duplicate": "AP Duplicate Detection - Identify duplicate invoices",
            "ar_register": "AR Invoice Register - List of all sales invoices",
            "ar_aging": "AR Aging Report - Aging analysis of receivables",
            "ar_collection": "AR Collection Priority - Prioritized collection list",
            "dso": "DSO Report - Days Sales Outstanding metrics"
        }