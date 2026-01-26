"""
AP Overdue Agent
Generates AP Overdue & SLA Breach report
"""

from typing import Dict, Any
from datetime import date
from processing_layer.agents.core.base_agent import BaseAgent, register_agent
from processing_layer.workflows.nodes import (
    InvoiceFetchNode,
    OutstandingCalculatorNode,
    AgingCalculatorNode,
    SLACheckerNode,
    FilterNode,
    SortNode,
    ExcelGeneratorNode
)


@register_agent
class APOverdueAgent(BaseAgent):
    """
    AP Overdue Agent
    
    Identifies overdue invoices and SLA breaches
    Prioritizes by severity (Low/Medium/High/Critical)
    """
    
    description = "AP Overdue & SLA - Identifies overdue invoices with SLA breaches"
    category = "ap_reports"
    
    def __init__(self):
        super().__init__("APOverdueAgent")
        
        # Initialize nodes
        self.invoice_fetch = InvoiceFetchNode()
        self.outstanding_calc = OutstandingCalculatorNode()
        self.aging_calc = AgingCalculatorNode()
        self.sla_checker = SLACheckerNode()
        self.filter_node = FilterNode()
        self.sort = SortNode()
        self.excel_gen = ExcelGeneratorNode()
    
    def execute(self, input_data: Any = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate AP Overdue Report
        
        Args:
            input_data: Optional input
            params: {
                'user_id': str,
                'sla_days': int (default: 30),
                'min_severity': str ('Low'|'Medium'|'High'|'Critical'),
                'min_amount': float
            }
            
        Returns:
            Report with overdue invoices
        """
        params = params or {}
        user_id = params.get('user_id', 'default')
        sla_days = params.get('sla_days', 30)
        min_severity = params.get('min_severity')
        min_amount = params.get('min_amount')
        
        # Debug logging
        print(f"DEBUG: APOverdueAgent received params: {params}")
        
        self._log_decision(
            f"Generate AP Overdue Report (SLA: {sla_days} days)",
            f"Min severity: {min_severity}, Min amount: {min_amount}"
        )
        
        # Fetch unpaid AP invoices
        filters = {'category': 'purchase', 'company_id': params.get('company_id')}
        
        self._log_node_call('InvoiceFetchNode', filters)
        invoices = self.invoice_fetch.run(params=filters)
        
        if not invoices:
            return {
                'status': 'success',
                'report_type': 'AP_OVERDUE',
                'message': 'No invoices found',
                'data': {}
            }
        
        # Calculate outstanding
        self._log_node_call('OutstandingCalculatorNode')
        invoices = self.outstanding_calc.run(invoices)
        
        # Filter to unpaid
        invoices = [
            inv for inv in invoices 
            if inv.get('status') in ['Unpaid', 'Partially Paid']
        ]
        
        # Calculate aging
        self._log_node_call('AgingCalculatorNode')
        invoices = self.aging_calc.run(invoices)
        
        # Check SLA
        self._log_node_call('SLACheckerNode', {'sla_days': sla_days})
        invoices = self.sla_checker.run(invoices, params={'sla_days': sla_days})
        
        # Filter to breached only
        breached_invoices = [inv for inv in invoices if inv.get('sla_breach', False)]
        
        self._log_decision(
            f"Found {len(breached_invoices)} SLA breaches",
            f"Out of {len(invoices)} total invoices"
        )
        
        # Apply severity filter
        if min_severity:
            severity_order = {'Low': 1, 'Medium': 2, 'High': 3, 'Critical': 4}
            min_level = severity_order.get(min_severity, 0)
            
            breached_invoices = [
                inv for inv in breached_invoices
                if severity_order.get(inv.get('sla_severity', 'None'), 0) >= min_level
            ]
            
            self._log_decision(
                f"Filter to {min_severity}+ severity",
                f"Remaining: {len(breached_invoices)} invoices"
            )
        
        # Apply amount filter
        if min_amount:
            breached_invoices = [
                inv for inv in breached_invoices
                if float(inv.get('outstanding', 0)) >= min_amount
            ]
            
            self._log_decision(
                f"Filter to amount >= {min_amount}",
                f"Remaining: {len(breached_invoices)} invoices"
            )
        
        # Sort by breach days (most overdue first)
        self._log_node_call('SortNode')
        breached_invoices = self.sort.run(
            breached_invoices,
            params={'sort_by': [{'field': 'breach_days', 'order': 'desc'}]}
        )
        
        # Calculate summary
        total_amount = sum(float(inv.get('outstanding', 0)) for inv in breached_invoices)
        
        by_severity = {}
        for inv in breached_invoices:
            severity = inv.get('sla_severity', 'None')
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        report_data = {
            'report_type': 'AP_OVERDUE',
            'sla_days': sla_days,
            'invoices': breached_invoices,
            'summary': {
                'total_breached': len(breached_invoices),
                'total_amount': round(total_amount, 2),
                'by_severity': by_severity
            }
        }
        
        # Generate Excel
        excel_params = {
            'user_id': user_id,
            'report_type': 'ap_overdue',
            'as_of_date': date.today().isoformat(),
            'sla_days': sla_days
        }
        self._log_node_call('ExcelGeneratorNode', excel_params)
        file_path = self.excel_gen.run(report_data, params=excel_params)
        
        return {
            'status': 'success',
            'report_type': 'AP_OVERDUE',
            'file_path': file_path,
            'data': report_data,
            'execution_history': self.get_execution_history()
        }