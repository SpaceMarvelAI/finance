"""
Final Fixed ExcelGeneratorNode with Report Metadata
"""

from processing_layer.workflows.nodes.base_node import BaseNode, register_node
from processing_layer.report_generation.branded_excel_generator import BrandedExcelGenerator
from typing import Dict, Any
from datetime import datetime, date


@register_node
class ExcelGeneratorNode(BaseNode):
    """
    Excel Generator Node
    Generates branded Excel reports using BrandedExcelGenerator
    """
    
    name = "Excel Generator"
    category = "output"
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            "description": "Generates branded Excel reports",
            "category": self.category,
            "input_schema": {
                "data": {"type": "any", "required": True},
                "user_id": {"type": "string", "required": True}
            },
            "output_schema": {
                "file_path": {"type": "string", "description": "Path to generated Excel file"}
            }
        }
    
    def run(self, input_data, params=None):
        """
        Generate Excel report
        
        Args:
            input_data: Report data (can be dict with invoices/groups/summary or list)
            params: {user_id, report_type, as_of_date}
        """
        params = params or {}
        user_id = params.get('user_id', 'spacemarvel')
        
        # Initialize generator
        generator = BrandedExcelGenerator(user_id)
        
        # Prepare report data with metadata
        report_data = self._prepare_report_data(input_data, params)
        
        # Determine report type and call appropriate method
        report_type = params.get('report_type', 'ap_aging')
        
        # Check for specific report types first (most specific to least specific)
        if report_type == 'ar_collection':
            file_path = generator.generate_ar_collection(report_data)
        elif report_type == 'ar_register' or report_type == 'ar_invoice_register':
            file_path = generator.generate_ar_invoice_register(report_data)
        elif report_type == 'ap_register' or report_type == 'ap_invoice_register':
            file_path = generator.generate_ap_invoice_register(report_data)
        elif report_type == 'ar_aging':
            file_path = generator.generate_ar_aging(report_data)
        elif report_type == 'ap_aging' or 'aging' in report_type.lower():
            file_path = generator.generate_ap_aging(report_data)
        elif report_type == 'ap_overdue' or 'overdue' in report_type.lower():
            sla_days = params.get('sla_days', 30)
            file_path = generator.generate_ap_overdue(report_data, sla_days=sla_days)
        elif report_type == 'dso':
            file_path = generator.generate_dso_report(report_data)
        else:
            # Default to aging
            file_path = generator.generate_ap_aging(report_data)
        
        return file_path
    
    def _prepare_report_data(self, input_data, params: Dict) -> Dict[str, Any]:
        """
        Prepare data in format expected by BrandedExcelGenerator
        
        BrandedExcelGenerator expects:
        {
            'invoices': [...],
            'summary': {...},
            'table_data': {
                'headers': [...],
                'rows': [...]
            },
            'report_metadata': {
                'as_of_date': '2025-01-12',
                'report_type': 'ap_aging',
                'generated_by': 'WorkflowPlannerAgent'
            }
        }
        """
        from datetime import date, datetime
        
        # Extract data based on input format
        invoices = []
        summary = {}
        groups = []
        
        if isinstance(input_data, dict):
            # Check if it has aging_data (from APAgingAgent/ARAgingAgent)
            if 'aging_data' in input_data:
                aging_data = input_data['aging_data']
                # aging_data is a dict with 'groups' key
                groups = aging_data.get('groups', [])
                for group in groups:
                    invoices.extend(group.get('records', []))
                summary = input_data.get('summary', {})
            
            # Check if it has groups directly (from GroupingNode)
            elif 'groups' in input_data:
                groups = input_data['groups']
                for group in groups:
                    invoices.extend(group.get('records', []))
                summary = input_data.get('summary', {})
            
            # Check if it has invoices directly
            elif 'invoices' in input_data:
                invoices = input_data['invoices']
                summary = input_data.get('summary', {})
            
            # Check if it has summary (from SummaryNode)
            elif 'summary' in input_data:
                summary = input_data['summary']
                # Try to get groups passed through
                if 'groups' in input_data:
                    groups = input_data['groups']
                    for group in groups:
                        invoices.extend(group.get('records', []))
            
            # Check if it's DSO data (direct DSO calculation result)
            elif 'dso' in input_data or ('data' in input_data and 'dso' in input_data['data']):
                # For DSO reports, we don't need invoices or table_data
                # Extract DSO data from the agent result
                dso_data = input_data['data'] if 'data' in input_data else input_data
                
                return dso_data  # Return DSO data directly for generate_dso_report
        
        # If it's a list, treat as invoices
        elif isinstance(input_data, list):
            invoices = input_data
        
        # Build table_data for AP Aging Report
        table_data = self._build_ap_aging_table(invoices, groups)
        
        # Build complete report data
        report_data = {
            'invoices': invoices,
            'summary': summary,
            'table_data': table_data,
            'report_metadata': {
                'as_of_date': params.get('as_of_date', date.today().isoformat()),
                'report_type': params.get('report_type', 'ap_aging'),
                'generated_by': 'WorkflowPlannerAgent',
                'generated_at': datetime.now().isoformat()
            }
        }
        
        return report_data
    
    def _build_ap_aging_table(self, invoices, groups=None):
        """
        Build table_data structure for AP Aging
        
        Format expected by BrandedExcelGenerator:
        {
            'headers': [...],
            'rows': [
                {
                    'vendor_name': 'Vendor A',
                    'invoice_no': 'INV001',
                    'due_date': '2025-01-15',
                    'total_due': 10000,
                    'current_0_30': 0,
                    'days_31_60': 0,
                    'days_61_90': 10000,
                    'days_90_plus': 0
                },
                ...
            ],
            'grand_totals': {
                'total_due': 50000,
                'current_0_30': 10000,
                'days_31_60': 15000,
                'days_61_90': 20000,
                'days_90_plus': 5000
            }
        }
        """
        # Determine if this is AP or AR based on invoice data
        is_ar = False
        if invoices and len(invoices) > 0:
            first_invoice = invoices[0]
            is_ar = 'customer_name' in first_invoice or 'customer_id' in first_invoice
        
        # Set appropriate header based on report type
        vendor_or_customer = 'Customer Name' if is_ar else 'Vendor Name'
        
        headers = [
            vendor_or_customer,
            'Invoice No.',
            'Due Date',
            'Total Due',
            'Current (0-30)',
            '31-60 Days',
            '61-90 Days',
            '90+ Days'
        ]
        
        rows = []
        
        # Initialize grand totals
        grand_totals = {
            'total_due': 0,
            'current_0_30': 0,
            'days_31_60': 0,
            'days_61_90': 0,
            'days_90_plus': 0
        }
        
        # If we have groups, organize by group
        if groups:
            self.logger.info(f"Building aging table from {len(groups)} groups")
            for group in groups:
                group_name = group.get('group_name', 'Unknown')
                group_records = group.get('records', [])
                
                self.logger.info(f"Processing group '{group_name}' with {len(group_records)} records")
                
                # Initialize group totals
                group_totals = {
                    'total_due': 0,
                    'current_0_30': 0,
                    'days_31_60': 0,
                    'days_61_90': 0,
                    'days_90_plus': 0
                }
                
                # Add group records
                for invoice in group_records:
                    row = self._invoice_to_aging_row_dict(invoice)
                    self.logger.info(f"  Row: {row['vendor_name']} - ₹{row['total_due']:,.2f} in bucket {group_name}")
                    rows.append(row)
                    
                    # Add to group totals
                    group_totals['total_due'] += row['total_due']
                    group_totals['current_0_30'] += row['current_0_30']
                    group_totals['days_31_60'] += row['days_31_60']
                    group_totals['days_61_90'] += row['days_61_90']
                    group_totals['days_90_plus'] += row['days_90_plus']
                
                # Add subtotal row for group
                subtotal_row = {
                    'vendor_name': f"Subtotal - {group_name}",
                    'invoice_no': '',
                    'due_date': '',
                    'total_due': group_totals['total_due'],
                    'current_0_30': group_totals['current_0_30'],
                    'days_31_60': group_totals['days_31_60'],
                    'days_61_90': group_totals['days_61_90'],
                    'days_90_plus': group_totals['days_90_plus']
                }
                rows.append(subtotal_row)
                
                # Add to grand totals
                grand_totals['total_due'] += group_totals['total_due']
                grand_totals['current_0_30'] += group_totals['current_0_30']
                grand_totals['days_31_60'] += group_totals['days_31_60']
                grand_totals['days_61_90'] += group_totals['days_61_90']
                grand_totals['days_90_plus'] += group_totals['days_90_plus']
        
        # No groups, just invoices
        else:
            for invoice in invoices:
                row = self._invoice_to_aging_row_dict(invoice)
                rows.append(row)
                
                # Add to grand totals
                grand_totals['total_due'] += row['total_due']
                grand_totals['current_0_30'] += row['current_0_30']
                grand_totals['days_31_60'] += row['days_31_60']
                grand_totals['days_61_90'] += row['days_61_90']
                grand_totals['days_90_plus'] += row['days_90_plus']
        
        return {
            'headers': headers,
            'rows': rows,
            'grand_totals': grand_totals
        }
    
    def _invoice_to_aging_row_dict(self, invoice):
        """
        Convert invoice dict to aging table row (as dict)
        
        CRITICAL: Database outstanding_amount might have original currency value
        We must ALWAYS calculate from INR amounts
        """
        aging_bucket = invoice.get('aging_bucket', 'Unknown')
        
        # ALWAYS calculate outstanding from INR amounts
        # Never trust outstanding_amount from database - it might be in original currency
        inr_total = float(invoice.get('inr_amount', 0) or invoice.get('total_amount', 0))
        paid = float(invoice.get('paid_amount', 0) or invoice.get('received_amount', 0))
        
        # Calculate outstanding in INR
        outstanding = inr_total - paid
        
        self.logger.info(f"Converting invoice: aging_bucket={aging_bucket}, inr_amount=₹{inr_total:,.2f}, outstanding=₹{outstanding:,.2f}")
        
        # Distribute amount to correct aging column
        current_0_30 = outstanding if aging_bucket == '0-30' else 0
        days_31_60 = outstanding if aging_bucket == '31-60' else 0
        days_61_90 = outstanding if aging_bucket == '61-90' else 0
        days_90_plus = outstanding if aging_bucket == '90+' else 0
        
        row = {
            'vendor_name': invoice.get('vendor_name', invoice.get('customer_name', 'Unknown')),
            'invoice_no': (
                invoice.get('invoice_number') or 
                invoice.get('document_number') or 
                ''
            ),
            'due_date': invoice.get('due_date', ''),
            'total_due': outstanding,
            'current_0_30': current_0_30,
            'days_31_60': days_31_60,
            'days_61_90': days_61_90,
            'days_90_plus': days_90_plus
        }
        
        self.logger.info(f"Created row: {row['vendor_name']} - ₹{row['total_due']:,.2f} in {aging_bucket} bucket")
        
        return row


@register_node
class GenericExcelGeneratorNode(BaseNode):
    """
    Generic Excel Generator
    Works without BrandedExcelGenerator for simple reports
    """
    
    name = "Generic Excel Generator"
    category = "output"
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            "description": "Generates simple Excel reports without branding",
            "category": self.category,
            "input_schema": {
                "data": {"type": "any", "required": True}
            },
            "output_schema": {
                "file_path": {"type": "string"}
            }
        }
    
    def run(self, input_data, params=None):
        """Generate simple Excel without branding"""
        import openpyxl
        from datetime import datetime
        import os
        
        params = params or {}
        user_id = params.get('user_id', 'default')
        
        # Create workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Report"
        
        # Extract data
        if isinstance(input_data, dict):
            invoices = input_data.get('invoices', input_data.get('records', []))
            summary = input_data.get('summary', {})
        elif isinstance(input_data, list):
            invoices = input_data
            summary = {}
        else:
            invoices = []
            summary = {}
        
        # Write headers
        if invoices:
            headers = list(invoices[0].keys())
            ws.append(headers)
            
            # Write data
            for invoice in invoices:
                ws.append([invoice.get(h, '') for h in headers])
        
        # Write summary
        if summary:
            ws.append([])
            ws.append(['Summary'])
            for key, value in summary.items():
                ws.append([key, value])
        
        # Save file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{user_id}_Report_{timestamp}.xlsx"
        
        # Save to current directory
        file_path = os.path.join(os.getcwd(), filename)
        wb.save(file_path)
        
        return file_path