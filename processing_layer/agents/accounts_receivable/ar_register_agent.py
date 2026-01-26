"""
AR Register Agent
Generates AR Invoice Register report
"""

from typing import Dict, Any
from processing_layer.agents.core.base_agent import BaseAgent, register_agent
from processing_layer.workflows.nodes import (
    InvoiceFetchNode,
    PaymentFetchNode,
    OutstandingCalculatorNode,
    SortNode,
    ExcelGeneratorNode
)


@register_agent
class ARRegisterAgent(BaseAgent):
    """
    AR Register Agent
    
    Generates comprehensive AR Invoice Register
    Shows all sales invoices with payment history
    """
    
    description = "AR Invoice Register - Complete list of sales invoices"
    category = "ar_reports"
    
    def __init__(self):
        super().__init__("ARRegisterAgent")
        
        # Initialize nodes
        self.invoice_fetch = InvoiceFetchNode()
        self.payment_fetch = PaymentFetchNode()
        self.outstanding_calc = OutstandingCalculatorNode()
        self.sort = SortNode()
        self.excel_gen = ExcelGeneratorNode()
    
    def execute(self, input_data: Any = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate AR Invoice Register
        
        Args:
            input_data: Optional input
            params: {
                'user_id': str,
                'date_from': str,
                'date_to': str,
                'include_closed': bool,
                'customer_ids': list
            }
            
        Returns:
            Report result with file path
        """
        params = params or {}
        user_id = params.get('user_id', 'default')
        include_closed = params.get('include_closed', True)
        
        self._log_decision(
            "Generate AR Invoice Register",
            f"Include closed: {include_closed}"
        )
        
        # Build filters
        filters = {
            'category': 'sales',
            'company_id': params.get('company_id')  # Pass company_id to nodes
        }
        
        if 'date_from' in params:
            filters['date_from'] = params['date_from']
        if 'date_to' in params:
            filters['date_to'] = params['date_to']
        if 'customer_ids' in params:
            filters['entity_ids'] = params['customer_ids']
        
        # Fetch invoices
        self._log_node_call('InvoiceFetchNode', filters)
        invoices = self.invoice_fetch.run(params=filters)
        
        if not invoices:
            return {
                'status': 'success',
                'report_type': 'AR_REGISTER',
                'message': 'No invoices found',
                'data': {}
            }
        
        # Calculate outstanding
        self._log_node_call('OutstandingCalculatorNode')
        invoices = self.outstanding_calc.run(invoices)
        
        # Filter closed if needed
        if not include_closed:
            self._log_decision(
                "Exclude fully collected invoices",
                "User requested open only"
            )
            invoices = [inv for inv in invoices if inv.get('status') != 'Paid']
        
        # Get payment history
        self._log_node_call('PaymentFetchNode')
        payments = self.payment_fetch.run(input_data=invoices)
        
        # Sort by date
        self._log_node_call('SortNode')
        invoices = self.sort.run(
            invoices,
            params={'sort_by': [{'field': 'document_date', 'order': 'desc'}]}
        )
        
        # Calculate summary
        total_amount = sum(float(inv.get('inr_amount', 0)) for inv in invoices)
        total_received = sum(float(inv.get('paid_amount', 0)) for inv in invoices)
        total_outstanding = total_amount - total_received
        
        report_data = {
            'report_type': 'AR_REGISTER',
            'invoices': invoices,
            'payments': payments,
            'summary': {
                'total_invoices': len(invoices),
                'total_amount': round(total_amount, 2),
                'total_received': round(total_received, 2),
                'total_outstanding': round(total_outstanding, 2)
            }
        }
        
        # Generate output
        self._log_node_call('ExcelGeneratorNode')
        file_path = self.excel_gen.run(report_data, params={
            'user_id': user_id,
            'report_type': 'ar_register'  # Specify AR Register, not aging
        })
        
        return {
            'status': 'success',
            'report_type': 'AR_REGISTER',
            'file_path': file_path,
            'data': report_data,
            'execution_history': self.get_execution_history()
        }