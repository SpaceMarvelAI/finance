"""
AR Collection Agent
Generates AR Collection Priority report
"""

from typing import Dict, Any
from processing_layer.agents.core.base_agent import BaseAgent, register_agent
from processing_layer.workflows.nodes import (
    InvoiceFetchNode,
    OutstandingCalculatorNode,
    AgingCalculatorNode,
    SLACheckerNode,
    SortNode,
    ExcelGeneratorNode
)


@register_agent
class ARCollectionAgent(BaseAgent):
    """
    AR Collection Agent
    
    Prioritizes collection efforts
    Calculates priority scores and recommends actions
    """
    
    description = "AR Collection Priority - Prioritized collection list with action recommendations"
    category = "ar_reports"
    
    def __init__(self):
        super().__init__("ARCollectionAgent")
        
        # Initialize nodes
        self.invoice_fetch = InvoiceFetchNode()
        self.outstanding_calc = OutstandingCalculatorNode()
        self.aging_calc = AgingCalculatorNode()
        self.sla_checker = SLACheckerNode()
        self.sort = SortNode()
        self.excel_gen = ExcelGeneratorNode()
    
    def execute(self, input_data: Any = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate Collection Priority Report
        
        Args:
            input_data: Optional input
            params: {
                'user_id': str,
                'sla_days': int,
                'top_n': int,
                'min_amount': float
            }
            
        Returns:
            Report with prioritized collection list
        """
        params = params or {}
        user_id = params.get('user_id', 'default')
        sla_days = params.get('sla_days', 30)
        top_n = params.get('top_n')
        min_amount = params.get('min_amount', 0)
        
        self._log_decision(
            f"Generate Collection Priority (SLA: {sla_days} days)",
            f"Top N: {top_n}, Min amount: {min_amount}"
        )
        
        # Fetch overdue AR invoices
        filters = {
            'category': 'sales',
            'company_id': params.get('company_id')
        }
        
        self._log_node_call('InvoiceFetchNode', filters)
        invoices = self.invoice_fetch.run(params=filters)
        
        if not invoices:
            return {
                'status': 'success',
                'report_type': 'AR_COLLECTION',
                'message': 'No invoices found',
                'data': {}
            }
        
        # Calculate outstanding
        self._log_node_call('OutstandingCalculatorNode')
        invoices = self.outstanding_calc.run(invoices)
        
        # Filter to outstanding
        invoices = [
            inv for inv in invoices 
            if inv.get('status') in ['Unpaid', 'Partially Paid']
        ]
        
        # Calculate aging
        self._log_node_call('AgingCalculatorNode')
        invoices = self.aging_calc.run(invoices)
        
        # Filter to overdue only
        overdue_invoices = [inv for inv in invoices if inv.get('overdue_days', 0) > 0]
        
        self._log_decision(
            f"Found {len(overdue_invoices)} overdue invoices",
            f"Out of {len(invoices)} total outstanding"
        )
        
        # Check SLA
        self._log_node_call('SLACheckerNode', {'sla_days': sla_days})
        overdue_invoices = self.sla_checker.run(overdue_invoices, params={'sla_days': sla_days})
        
        # Calculate priority scores
        self._log_decision(
            "Calculating priority scores",
            "Formula: Outstanding × Overdue Days × SLA Multiplier"
        )
        
        for inv in overdue_invoices:
            outstanding = float(inv.get('outstanding', 0))
            overdue_days = inv.get('overdue_days', 0)
            sla_breach = inv.get('sla_breach', False)
            
            # Priority formula
            sla_multiplier = 2.0 if sla_breach else 1.0
            priority_score = outstanding * overdue_days * sla_multiplier
            
            inv['priority_score'] = round(priority_score, 2)
            
            # Action recommendation
            if sla_breach and outstanding > 50000:
                inv['action'] = "URGENT - Legal escalation"
                inv['priority'] = "Critical"
            elif sla_breach and outstanding > 10000:
                inv['action'] = "Call immediately + escalate to manager"
                inv['priority'] = "Critical"
            elif sla_breach:
                inv['action'] = "Call customer today"
                inv['priority'] = "High"
            elif overdue_days > 15:
                inv['action'] = "Send final notice + call"
                inv['priority'] = "Medium"
            else:
                inv['action'] = "Send payment reminder"
                inv['priority'] = "Low"
        
        # Filter by minimum amount
        if min_amount > 0:
            overdue_invoices = [
                inv for inv in overdue_invoices
                if float(inv.get('outstanding', 0)) >= min_amount
            ]
            
            self._log_decision(
                f"Filtered to amount >= {min_amount}",
                f"Remaining: {len(overdue_invoices)} invoices"
            )
        
        # Sort by priority score
        self._log_node_call('SortNode')
        overdue_invoices = self.sort.run(
            overdue_invoices,
            params={'sort_by': [{'field': 'priority_score', 'order': 'desc'}]}
        )
        
        # Limit to top N
        if top_n and top_n > 0:
            self._log_decision(
                f"Limit to top {top_n} priorities",
                "Focus on highest impact accounts"
            )
            overdue_invoices = overdue_invoices[:top_n]
        
        # Calculate summary
        total_outstanding = sum(float(inv.get('outstanding', 0)) for inv in overdue_invoices)
        
        by_priority = {}
        for inv in overdue_invoices:
            priority = inv.get('priority', 'Unknown')
            by_priority[priority] = by_priority.get(priority, 0) + 1
        
        report_data = {
            'report_type': 'AR_COLLECTION',
            'sla_days': sla_days,
            'invoices': overdue_invoices,
            'summary': {
                'total_overdue': len(overdue_invoices),
                'total_outstanding': round(total_outstanding, 2),
                'by_priority': by_priority
            }
        }
        
        # Generate Excel
        self._log_node_call('ExcelGeneratorNode')
        file_path = self.excel_gen.run(report_data, params={
            'user_id': user_id,
            'report_type': 'ar_collection'
        })
        
        return {
            'status': 'success',
            'report_type': 'AR_COLLECTION',
            'file_path': file_path,
            'data': report_data,
            'execution_history': self.get_execution_history()
        }