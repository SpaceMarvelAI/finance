"""
AP Aging Agent
Generates AP Aging Analysis report
"""

from typing import Dict, Any
from datetime import datetime
from processing_layer.agents.core.base_agent import BaseAgent, register_agent
from processing_layer.workflows.nodes import (
    InvoiceFetchNode,
    OutstandingCalculatorNode,
    AgingCalculatorNode,
    FilterNode,
    GroupingNode,
    SummaryNode,
    ExcelGeneratorNode
)


@register_agent
class APAgingAgent(BaseAgent):
    """
    AP Aging Agent
    
    Generates aging analysis of accounts payable
    Groups by aging buckets (0-30, 31-60, 61-90, 90+)
    """
    
    description = "AP Aging Report - Aging analysis of payables"
    category = "ap_reports"
    
    def __init__(self):
        super().__init__("APAgingAgent")
        
        # Initialize nodes
        self.invoice_fetch = InvoiceFetchNode()
        self.outstanding_calc = OutstandingCalculatorNode()
        self.aging_calc = AgingCalculatorNode()
        self.filter_node = FilterNode()
        self.grouping = GroupingNode()
        self.summary = SummaryNode()
        self.excel_gen = ExcelGeneratorNode()
    
    def execute(self, input_data: Any = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate AP Aging Report
        
        Args:
            input_data: Optional input
            params: {
                'user_id': str,
                'as_of_date': str,
                'include_paid': bool,
                'min_aging_days': int
            }
            
        Returns:
            Report result with aging analysis
        """
        params = params or {}
        user_id = params.get('user_id', 'default')
        as_of_date = params.get('as_of_date', datetime.now().date().isoformat())
        include_paid = params.get('include_paid', False)
        min_aging_days = params.get('min_aging_days', 0)
        
        self._log_decision(
            "Generate AP Aging Report",
            f"As of: {as_of_date}, Include paid: {include_paid}"
        )
        
        # Fetch AP invoices
        filters = {
            'category': 'purchase',
            'company_id': params.get('company_id')
        }

        self._log_node_call('InvoiceFetchNode', filters)
        invoices = self.invoice_fetch.run(params=filters)
        
        if not invoices:
            return {
                'status': 'success',
                'report_type': 'AP_AGING',
                'message': 'No invoices found',
                'data': {}
            }
        
        # Calculate outstanding
        self._log_node_call('OutstandingCalculatorNode')
        invoices = self.outstanding_calc.run(invoices)
        
        # Filter to unpaid/partially paid
        if not include_paid:
            self._log_decision(
                "Filter to outstanding invoices",
                "Exclude fully paid invoices"
            )
            invoices = [
                inv for inv in invoices 
                if inv.get('status') in ['Unpaid', 'Partially Paid']
            ]
        
        # Calculate aging
        self._log_node_call('AgingCalculatorNode', {'as_of_date': as_of_date})
        invoices = self.aging_calc.run(invoices, params={'as_of_date': as_of_date})
        
        # Filter by minimum aging days
        if min_aging_days > 0:
            self._log_decision(
                f"Filter to invoices aged {min_aging_days}+ days",
                "User specified minimum aging threshold"
            )
            invoices = [
                inv for inv in invoices 
                if inv.get('aging_days', 0) >= min_aging_days
            ]
        
        # Group by aging bucket
        self._log_node_call('GroupingNode', {'group_by': 'aging_bucket'})
        grouped = self.grouping.run(invoices, params={'group_by': 'aging_bucket'})
        
        # Calculate summary
        self._log_node_call('SummaryNode')
        summary = self.summary.run(invoices)
        
        report_data = {
            'report_type': 'AP_AGING',
            'as_of_date': as_of_date,
            'aging_data': grouped,
            'summary': summary,
            'total_invoices': len(invoices)
        }
        
        # Generate Excel
        self._log_node_call('ExcelGeneratorNode')
        file_path = self.excel_gen.run(report_data, params={'user_id': user_id})
        
        return {
            'status': 'success',
            'report_type': 'AP_AGING',
            'file_path': file_path,
            'data': report_data,
            'execution_history': self.get_execution_history()
        }