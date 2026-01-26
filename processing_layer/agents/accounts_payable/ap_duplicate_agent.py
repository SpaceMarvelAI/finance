"""
AP Duplicate Agent
Detects duplicate invoices
"""

from typing import Dict, Any
from processing_layer.agents.core.base_agent import BaseAgent, register_agent
from processing_layer.workflows.nodes import (
    InvoiceFetchNode,
    DuplicateDetectorNode,
    ExcelGeneratorNode
)


@register_agent
class APDuplicateAgent(BaseAgent):
    """
    AP Duplicate Agent
    
    Detects exact and fuzzy duplicate invoices
    Prevents duplicate payments
    """
    
    description = "AP Duplicate Detection - Identifies duplicate invoices"
    category = "ap_reports"
    
    def __init__(self):
        super().__init__("APDuplicateAgent")
        
        # Initialize nodes
        self.invoice_fetch = InvoiceFetchNode()
        self.duplicate_detector = DuplicateDetectorNode()
        self.excel_gen = ExcelGeneratorNode()
    
    def execute(self, input_data: Any = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Detect duplicate invoices
        
        Args:
            input_data: Optional input
            params: {
                'user_id': str,
                'tolerance': float (default: 0.01),
                'min_confidence': int (75|100)
            }
            
        Returns:
            Report with duplicate groups
        """
        params = params or {}
        user_id = params.get('user_id', 'default')
        tolerance = params.get('tolerance', 0.01)
        min_confidence = params.get('min_confidence', 75)
        
        self._log_decision(
            "Detect AP invoice duplicates",
            f"Tolerance: {tolerance}, Min confidence: {min_confidence}%"
        )
        
        # Fetch all AP invoices
        filters = {'category': 'purchase'}
        
        self._log_node_call('InvoiceFetchNode', filters)
        invoices = self.invoice_fetch.run(params=filters)
        
        if not invoices:
            return {
                'status': 'success',
                'report_type': 'AP_DUPLICATE',
                'message': 'No invoices found',
                'data': {}
            }
        
        self._log_decision(
            f"Scanning {len(invoices)} invoices for duplicates",
            "Checking exact and fuzzy matches"
        )
        
        # Detect duplicates
        self._log_node_call('DuplicateDetectorNode', {'tolerance': tolerance})
        duplicates = self.duplicate_detector.run(invoices, params={'tolerance': tolerance})
        
        exact = duplicates.get('exact_duplicates', [])
        fuzzy = duplicates.get('fuzzy_duplicates', [])
        
        # Filter by confidence
        if min_confidence > 75:
            self._log_decision(
                f"Show only exact matches (confidence 100%)",
                "User requested high confidence threshold"
            )
            fuzzy = []
        
        total_exact = len(exact)
        total_fuzzy = len(fuzzy)
        total_affected = sum(len(dup['group']) for dup in exact + fuzzy)
        
        self._log_decision(
            f"Found {total_exact} exact + {total_fuzzy} fuzzy duplicates",
            f"Total affected invoices: {total_affected}"
        )
        
        report_data = {
            'report_type': 'AP_DUPLICATE',
            'tolerance': tolerance,
            'min_confidence': min_confidence,
            'exact_duplicates': exact,
            'fuzzy_duplicates': fuzzy,
            'summary': {
                'total_exact': total_exact,
                'total_fuzzy': total_fuzzy,
                'total_affected': total_affected
            }
        }
        
        # Generate Excel
        self._log_node_call('ExcelGeneratorNode')
        file_path = self.excel_gen.run(report_data, params={'user_id': user_id})
        
        return {
            'status': 'success',
            'report_type': 'AP_DUPLICATE',
            'file_path': file_path,
            'data': report_data,
            'execution_history': self.get_execution_history()
        }