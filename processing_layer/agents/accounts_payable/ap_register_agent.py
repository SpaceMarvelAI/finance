"""
AP Register Agent
Generates AP Invoice Register report
"""

from typing import Dict, Any
from processing_layer.agents.core.base_agent import BaseAgent, register_agent
from processing_layer.workflows.nodes import (
    InvoiceFetchNode,
    OutstandingCalculatorNode,
    SortNode,
    ExcelGeneratorNode
)


@register_agent
class APRegisterAgent(BaseAgent):
    """
    AP Register Agent
    
    Generates comprehensive AP Invoice Register
    Shows all purchase invoices with outstanding amounts
    """
    
    description = "AP Invoice Register - Complete list of purchase invoices"
    category = "ap_reports"
    
    def __init__(self):
        super().__init__("APRegisterAgent")
        
        # Initialize nodes
        self.invoice_fetch = InvoiceFetchNode()
        self.outstanding_calc = OutstandingCalculatorNode()
        self.sort = SortNode()
        self.excel_gen = ExcelGeneratorNode()
    
    def execute(self, input_data: Any = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate AP Invoice Register
        
        Args:
            input_data: Optional input
            params: {
                'user_id': str,
                'date_from': str,
                'date_to': str,
                'include_paid': bool,
                'vendor_ids': list
            }
            
        Returns:
            Report result with file path
        """
        params = params or {}
        user_id = params.get('user_id', 'default')
        include_paid = params.get('include_paid', True)
        
        self._log_decision(
            "Generate AP Invoice Register",
            f"Include paid: {include_paid}"
        )
        
        # Build filters
        filters = {
            'category': 'purchase',
            'company_id': params.get('company_id')  # Pass company_id to nodes
        }
        
        if 'date_from' in params:
            filters['date_from'] = params['date_from']
        if 'date_to' in params:
            filters['date_to'] = params['date_to']
        if 'vendor_ids' in params:
            filters['entity_ids'] = params['vendor_ids']
        
        # Fetch invoices
        self._log_node_call('InvoiceFetchNode', filters)
        invoices = self.invoice_fetch.run(params=filters)
        
        if not invoices:
            return {
                'status': 'success',
                'report_type': 'AP_REGISTER',
                'message': 'No invoices found',
                'data': {'invoices': [], 'summary': {}}
            }
        
        # Calculate outstanding
        self._log_node_call('OutstandingCalculatorNode')
        invoices = self.outstanding_calc.run(invoices)
        
        # Filter paid if needed
        if not include_paid:
            self._log_decision(
                "Exclude fully paid invoices",
                "User requested unpaid only"
            )
            invoices = [inv for inv in invoices if inv.get('status') != 'Paid']
        
        # Sort by date
        self._log_node_call('SortNode')
        invoices = self.sort.run(
            invoices,
            params={'sort_by': [{'field': 'document_date', 'order': 'desc'}]}
        )
        
        # Transform data for Excel template using DataTransformationNode
        self._log_node_call('DataTransformationNode')
        from processing_layer.workflows.nodes.calculation_nodes import DataTransformationNode
        transformer = DataTransformationNode()
        transformed_invoices = transformer.run(invoices)
        
        # Calculate totals using TotalsCalculationNode
        self._log_node_call('TotalsCalculationNode')
        from processing_layer.workflows.nodes.calculation_nodes import TotalsCalculationNode
        totals_calc = TotalsCalculationNode()
        totals = totals_calc.run(transformed_invoices)
        
        # Calculate summary statistics
        total_amount = sum(float(inv.get('inr_amount', 0)) for inv in invoices)
        total_outstanding_sum = sum(float(inv.get('outstanding', 0)) for inv in invoices)
        total_paid = total_amount - total_outstanding_sum
        
        # Count by status
        paid_count = sum(1 for inv in transformed_invoices if inv['status'] == 'Paid')
        unpaid_count = sum(1 for inv in transformed_invoices if inv['status'] == 'Unpaid')
        partial_count = sum(1 for inv in transformed_invoices if inv['status'] == 'Partial')
        
        report_data = {
            'report_type': 'AP_REGISTER',
            'invoices': transformed_invoices,
            'summary': {
                'total_invoices': len(invoices),
                'total_amount': round(total_amount, 2),
                'total_paid': round(total_paid, 2),
                'total_outstanding': round(total_outstanding_sum, 2),
                'paid_count': paid_count,
                'unpaid_count': unpaid_count,
                'partial_count': partial_count
            },
            'totals': totals
        }
        
        # Generate output
        self._log_node_call('ExcelGeneratorNode')
        file_path = self.excel_gen.run(report_data, params={
            'user_id': user_id,
            'report_type': 'ap_register'  # CRITICAL: Tell Excel generator what report to make
        })
        
        return {
            'status': 'success',
            'report_type': 'AP_REGISTER',
            'file_path': file_path,
            'data': report_data,
            'execution_history': self.get_execution_history()
        }