"""
DSO Agent - Days Sales Outstanding Calculator
Calculates average collection period for accounts receivable
"""

from typing import Dict, Any
from datetime import datetime, timedelta, date
from decimal import Decimal
from processing_layer.agents.core.base_agent import BaseAgent, register_agent
from processing_layer.workflows.nodes import InvoiceFetchNode, ExcelGeneratorNode


@register_agent
class DSOAgent(BaseAgent):
    """
    DSO (Days Sales Outstanding) Agent
    
    Calculates average number of days it takes to collect payment after a sale
    Formula: DSO = (Average AR / Total Credit Sales) × Number of Days
    
    Lower DSO = Faster collection = Better cash flow
    """
    
    description = "DSO Calculator - Measures accounts receivable collection efficiency"
    category = "ar_reports"
    
    def __init__(self):
        super().__init__("DSOAgent")
        self.invoice_fetch = InvoiceFetchNode()
        self.excel_gen = ExcelGeneratorNode()
    
    def execute(self, input_data: Any = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Calculate DSO
        
        Args:
            input_data: Optional input
            params: {
                'user_id': str,
                'company_id': str,
                'period_days': int (default: 90),
                'date_from': str,
                'date_to': str
            }
            
        Returns:
            DSO calculation result
        """
        params = params or {}
        period_days = params.get('period_days', 90)
        
        # Calculate date range
        if 'date_to' in params:
            end_date = datetime.fromisoformat(params['date_to']).date()
        else:
            end_date = date.today()
        
        if 'date_from' in params:
            start_date = datetime.fromisoformat(params['date_from']).date()
        else:
            start_date = end_date - timedelta(days=period_days)
        
        self._log_decision(
            f"Calculate DSO over {period_days} day period",
            f"Formula: (Average AR / Total Sales) × Period Days"
        )
        
        # Fetch AR invoices for the period
        filters = {
            'category': 'sales',
            'date_from': start_date.isoformat(),
            'date_to': end_date.isoformat()
        }
        
        if 'company_id' in params:
            filters['company_id'] = params['company_id']
        
        self._log_node_call('InvoiceFetchNode', filters)
        invoices = self.invoice_fetch.run(params=filters)
        
        if not invoices:
            return {
                'status': 'success',
                'report_type': 'DSO',
                'message': 'No sales invoices found for the period',
                'dso': 0,
                'data': {
                    'period_days': period_days,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'total_sales': 0,
                    'average_ar': 0,
                    'invoice_count': 0
                }
            }
        
        # Calculate total sales (credit sales in INR)
        total_sales = Decimal('0')
        total_outstanding = Decimal('0')
        
        for invoice in invoices:
            # Use INR amount for calculations
            inr_amount = Decimal(str(invoice.get('inr_amount', 0)))
            outstanding = Decimal(str(invoice.get('outstanding_amount', inr_amount)))
            
            total_sales += inr_amount
            total_outstanding += outstanding
        
        # Calculate average AR
        # For simplicity, use current outstanding as average
        # (In production, you'd want beginning + ending AR / 2)
        average_ar = total_outstanding
        
        # Calculate DSO
        if total_sales > 0:
            dso = float((average_ar / total_sales) * Decimal(str(period_days)))
        else:
            dso = 0
        
        self._log_decision(
            f"DSO Calculated: {dso:.1f} days",
            f"Sales: ₹{float(total_sales):,.2f}, Avg AR: ₹{float(average_ar):,.2f}"
        )
        
        # Categorize DSO performance
        if dso <= 30:
            performance = "Excellent"
            category = "success"
        elif dso <= 45:
            performance = "Good"
            category = "success"
        elif dso <= 60:
            performance = "Fair"
            category = "warning"
        else:
            performance = "Needs Improvement"
            category = "danger"
        
        result_data = {
            'dso': round(dso, 1),
            'performance': performance,
            'category': category,
            'period_days': period_days,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_sales': round(float(total_sales), 2),
            'average_ar': round(float(average_ar), 2),
            'outstanding_ar': round(float(total_outstanding), 2),
            'invoice_count': len(invoices),
            'paid_invoices': sum(1 for inv in invoices if inv.get('status') == 'Paid'),
            'unpaid_invoices': sum(1 for inv in invoices if inv.get('status') == 'Unpaid')
        }
        
        # Generate DSO report
        self._log_node_call('ExcelGeneratorNode', {'report_type': 'dso'})
        file_path = self.excel_gen.run(result_data, params={
            'user_id': params.get('user_id', 'spacemarvel'),
            'report_type': 'dso',
            'as_of_date': end_date.isoformat()
        })
        
        return {
            'status': 'success',
            'report_type': 'DSO',
            'file_path': file_path,
            'message': f"DSO: {dso:.1f} days - {performance}",
            'data': result_data,
            'execution_history': self.get_execution_history()
        }
