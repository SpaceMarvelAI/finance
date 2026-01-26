"""
AR Aging Agent - Complete Working Version
Generates AR Aging Analysis report for customer invoices
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
class ARAgingAgent(BaseAgent):
    """
    AR Aging Agent
    
    Generates aging analysis of accounts receivable
    Groups customer invoices by aging buckets (0-30, 31-60, 61-90, 90+)
    """
    
    description = "AR Aging Report - Aging analysis of receivables"
    category = "ar_reports"
    
    def __init__(self):
        super().__init__("ARAgingAgent")
        
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
        Generate AR Aging Report
        
        Args:
            input_data: Optional input
            params: {
                'user_id': str,
                'company_id': str,
                'as_of_date': str,
                'group_by': str (default: 'aging_bucket'),
                'min_aging_days': int
            }
            
        Returns:
            Report result with aging analysis
        """
        params = params or {}
        user_id = params.get('user_id', 'default')
        as_of_date = params.get('as_of_date', datetime.now().date().isoformat())
        group_by = params.get('group_by', 'aging_bucket')
        min_aging_days = params.get('min_aging_days', 0)
        
        self._log_decision(
            f"Generate AR Aging Report (group by: {group_by})",
            f"As of: {as_of_date}"
        )
        
        # Fetch AR invoices
        filters = {
            'category': 'sales',
            'company_id': params.get('company_id')
        }
        
        self._log_node_call('InvoiceFetchNode', filters)
        invoices = self.invoice_fetch.run(params=filters)
        
        if not invoices:
            return {
                'status': 'success',
                'report_type': 'AR_AGING',
                'message': 'No invoices found',
                'data': {}
            }
        
        # Calculate outstanding
        self._log_node_call('OutstandingCalculatorNode')
        invoices = self.outstanding_calc.run(invoices)
        
        # Filter to outstanding only
        self._log_decision(
            f"Found {len(invoices)} outstanding AR invoices",
            "Calculating aging"
        )
        
        # Calculate aging
        self._log_node_call('AgingCalculatorNode', {'as_of_date': as_of_date})
        invoices = self.aging_calc.run(invoices, params={'as_of_date': as_of_date})
        
        # Filter by minimum aging days if specified
        if min_aging_days > 0:
            self._log_decision(
                f"Filter to invoices aged {min_aging_days}+ days",
                "User specified minimum aging threshold"
            )
            invoices = [
                inv for inv in invoices 
                if inv.get('aging_days', 0) >= min_aging_days
            ]
        
        # Group by aging bucket or other field
        self._log_node_call('GroupingNode', {'group_by': group_by})
        grouped = self.grouping.run(invoices, params={'group_by': group_by})
        
        # Calculate summary
        self._log_node_call('SummaryNode')
        summary = self.summary.run(invoices)
        
        report_data = {
            'report_type': 'AR_AGING',
            'as_of_date': as_of_date,
            'aging_data': grouped,
            'summary': summary,
            'total_invoices': len(invoices)
        }
        
        # Generate Excel
        self._log_node_call('ExcelGeneratorNode')
        file_path = self.excel_gen.run(report_data, params={
            'user_id': user_id,
            'report_type': 'ar_aging'  # IMPORTANT: Tell Excel generator this is AR aging
        })
        
        return {
            'status': 'success',
            'report_type': 'AR_AGING',
            'file_path': file_path,
            'data': report_data,
            'execution_history': self.get_execution_history()
        }