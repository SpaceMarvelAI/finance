"""
CALCULATION NODES - Pure Math Functions
No decisions, just calculations
"""

from typing import Dict, Any, List
from datetime import datetime, date
from decimal import Decimal
from processing_layer.workflows.nodes.base_node import BaseNode, register_node


@register_node
class TotalsCalculationNode(BaseNode):
    """
    Totals Calculation Node
    Pure function to calculate totals/summary for reports
    """
    
    name = "Totals Calculator"
    category = "calculation"
    description = "Calculates totals and summary statistics for invoices"
    
    input_schema = {
        "invoices": {"type": "array"}
    }
    
    output_schema = {
        "totals": {"type": "object", "description": "Calculated totals"}
    }
    
    def run(self, input_data: List[Dict], params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Calculate totals from invoices
        
        Returns totals compatible with Excel templates
        """
        if not input_data:
            return {
                'invoice_amt': 0,
                'tax_amt': 0,
                'net_amt': 0,
                'paid_amt': 0,
                'outstanding': 0
            }
        
        total_invoice_amt = 0
        total_tax_amt = 0
        total_paid_amt = 0
        total_outstanding = 0
        
        for inv in input_data:
            invoice_amt = float(inv.get('invoice_amt', inv.get('grand_total', inv.get('inr_amount', 0))))
            tax_amt = float(inv.get('tax_amt', inv.get('tax_total', 0)))
            outstanding = float(inv.get('outstanding', 0))
            paid_amt = invoice_amt - outstanding
            
            total_invoice_amt += invoice_amt
            total_tax_amt += tax_amt
            total_paid_amt += paid_amt
            total_outstanding += outstanding
        
        return {
            'invoice_amt': round(total_invoice_amt - total_tax_amt, 2),  # Net amount (subtotal)
            'tax_amt': round(total_tax_amt, 2),
            'net_amt': round(total_invoice_amt, 2),  # Invoice amount (total)
            'paid_amt': round(total_paid_amt, 2),
            'outstanding': round(total_outstanding, 2)
        }


@register_node
class AgingCalculatorNode(BaseNode):
    """
    Aging Calculator Node
    Pure function to calculate invoice aging
    
    Used by 6 reports according to document
    """
    
    name = "Aging Calculator"
    category = "calculation"
    description = "Calculates aging days and assigns buckets (0-30, 31-60, 61-90, 90+)"
    
    input_schema = {
        "invoices": {"type": "array"},
        "as_of_date": {"type": "date", "description": "Date to calculate aging from"}
    }
    
    output_schema = {
        "invoices": {"type": "array", "description": "Invoices with aging_days and aging_bucket"}
    }
    
    def run(self, input_data: List[Dict], params: Dict[str, Any] = None) -> List[Dict]:
        """
        Calculate aging for invoices
        
        Formula from document:
        - Aging Days = Current Date - Invoice Date
        - Overdue Days = Current Date - Due Date
        - Bucket: 0-30, 31-60, 61-90, 90+
        
        Args:
            input_data: List of invoices
            params: as_of_date (defaults to today)
            
        Returns:
            Invoices with aging fields added
        """
        if not input_data:
            return []
        
        params = params or {}
        as_of_date = params.get('as_of_date')
        
        if isinstance(as_of_date, str):
            as_of_date = datetime.fromisoformat(as_of_date).date()
        elif not as_of_date:
            as_of_date = date.today()
        
        for invoice in input_data:
            # Get invoice date - support multiple field names
            invoice_date_str = (
                invoice.get('invoice_date') or 
                invoice.get('document_date') or
                invoice.get('date')
            )
            
            if not invoice_date_str:
                self.logger.warning(f"Invoice {invoice.get('id', 'unknown')} has no date, setting Unknown bucket")
                invoice['aging_days'] = 0
                invoice['aging_bucket'] = "Unknown"
                continue
            
            # Parse date - handle multiple formats
            try:
                if isinstance(invoice_date_str, date):
                    invoice_date = invoice_date_str
                elif isinstance(invoice_date_str, datetime):
                    invoice_date = invoice_date_str.date()
                elif isinstance(invoice_date_str, str):
                    # Try ISO format first
                    try:
                        invoice_date = datetime.fromisoformat(invoice_date_str.replace('Z', '+00:00')).date()
                    except:
                        # Try parsing as date only
                        invoice_date = datetime.strptime(invoice_date_str, '%Y-%m-%d').date()
                else:
                    raise ValueError(f"Unknown date type: {type(invoice_date_str)}")
                    
            except Exception as e:
                self.logger.error(f"Failed to parse date '{invoice_date_str}': {e}")
                invoice['aging_days'] = 0
                invoice['aging_bucket'] = "Unknown"
                continue
            
            # Calculate aging days (pure math)
            aging_days = (as_of_date - invoice_date).days
            invoice['aging_days'] = aging_days
            
            # Calculate overdue days
            due_date_str = invoice.get('due_date')
            if due_date_str:
                try:
                    if isinstance(due_date_str, date):
                        due_date = due_date_str
                    elif isinstance(due_date_str, datetime):
                        due_date = due_date_str.date()
                    elif isinstance(due_date_str, str):
                        try:
                            due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).date()
                        except:
                            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                    overdue_days = (as_of_date - due_date).days
                    invoice['overdue_days'] = overdue_days
                except Exception as e:
                    self.logger.warning(f"Failed to parse due_date '{due_date_str}': {e}")
                    invoice['overdue_days'] = 0
            else:
                invoice['overdue_days'] = 0
            
            # Assign bucket (pure logic - no decisions)
            if aging_days <= 30:
                bucket = "0-30"
            elif aging_days <= 60:
                bucket = "31-60"
            elif aging_days <= 90:
                bucket = "61-90"
            else:
                bucket = "90+"
            
            invoice['aging_bucket'] = bucket
            self.logger.info(f"Invoice {invoice.get('invoice_number', 'N/A')}: {aging_days} days old → bucket {bucket}")
        
        self.logger.info(f"Calculated aging for {len(input_data)} invoices")
        return input_data


@register_node
class OutstandingCalculatorNode(BaseNode):
    """
    Outstanding Calculator Node
    Pure function to calculate outstanding amounts
    
    Used by 10 reports according to document
    """
    
    name = "Outstanding Calculator"
    category = "calculation"
    description = "Calculates outstanding amount and invoice status"
    
    input_schema = {
        "invoices": {"type": "array"}
    }
    
    output_schema = {
        "invoices": {"type": "array", "description": "Invoices with outstanding and status"}
    }
    
    def run(self, input_data: List[Dict], params: Dict[str, Any] = None) -> List[Dict]:
        """
        Calculate outstanding amounts
        
        Formulas from document:
        - Outstanding = Invoice Total - Amount Paid
        - Gross = Total - Tax
        - Status: Paid / Partially Paid / Unpaid
        
        Args:
            input_data: List of invoices
            params: Not used
            
        Returns:
            Invoices with outstanding fields added
        """
        if not input_data:
            return []
        
        for invoice in input_data:
            # Get amounts - ALWAYS use INR amounts for calculations
            total = float(invoice.get('inr_amount') or invoice.get('total_amount', 0) or invoice.get('grand_total', 0))
            paid = float(invoice.get('paid_amount', 0) or invoice.get('received_amount', 0))
            tax = float(invoice.get('tax_amount', 0) or invoice.get('tax_total', 0))
            
            # Calculate outstanding (pure math)
            outstanding = total - paid
            # Set both field names for compatibility
            invoice['outstanding'] = round(outstanding, 2)
            invoice['outstanding_amount'] = round(outstanding, 2)
            
            # Calculate gross (pure math)
            gross = total - tax
            invoice['gross_amount'] = round(gross, 2)
            
            # Determine status (pure logic - no decisions)
            if paid >= total:
                status = "Paid"
            elif paid <= 0:
                status = "Unpaid"
            else:
                status = "Partially Paid"
            
            invoice['status'] = status
        
        self.logger.info(f"Calculated outstanding for {len(input_data)} invoices")
        return input_data


@register_node
class SLACheckerNode(BaseNode):
    """
    SLA Checker Node
    Pure function to check SLA breaches
    
    Used by 3 reports according to document
    """
    
    name = "SLA Checker"
    category = "calculation"
    description = "Checks SLA breaches and calculates severity"
    
    input_schema = {
        "invoices": {"type": "array"},
        "sla_days": {"type": "number", "description": "SLA threshold in days"}
    }
    
    output_schema = {
        "invoices": {"type": "array", "description": "Invoices with SLA breach info"}
    }
    
    def run(self, input_data: List[Dict], params: Dict[str, Any] = None) -> List[Dict]:
        """
        Check SLA breaches
        
        Formulas from document:
        - SLA Deadline = Due Date + SLA Threshold
        - Breach = Current Date > SLA Deadline
        - Severity: None/Low/Medium/High/Critical
        
        Args:
            input_data: List of invoices
            params: sla_days threshold
            
        Returns:
            Invoices with SLA fields added
        """
        if not input_data:
            return []
        
        params = params or {}
        sla_days = params.get('sla_days', 30)
        today = date.today()
        
        for invoice in input_data:
            # Get due date
            due_date_str = invoice.get('due_date')
            if not due_date_str:
                invoice['sla_breach'] = False
                invoice['sla_severity'] = "None"
                invoice['breach_days'] = 0
                continue
            
            # Parse date
            if isinstance(due_date_str, str):
                due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00')).date()
            else:
                due_date = due_date_str
            
            # Calculate SLA deadline (pure math)
            from datetime import timedelta
            sla_deadline = due_date + timedelta(days=sla_days)
            
            # Check breach (pure logic)
            breach = today > sla_deadline
            invoice['sla_breach'] = breach
            
            if breach:
                breach_days = (today - sla_deadline).days
                invoice['breach_days'] = breach_days
                
                # Calculate severity (pure logic - no decisions)
                if breach_days <= 7:
                    severity = "Low"
                elif breach_days <= 14:
                    severity = "Medium"
                elif breach_days <= 30:
                    severity = "High"
                else:
                    severity = "Critical"
                
                invoice['sla_severity'] = severity
            else:
                invoice['breach_days'] = 0
                invoice['sla_severity'] = "None"
        
        self.logger.info(f"Checked SLA for {len(input_data)} invoices")
        return input_data


@register_node
class DuplicateDetectorNode(BaseNode):
    """
    Duplicate Detector Node
    Pure function to detect duplicate invoices
    
    Used by 2+ reports according to document
    """
    
    name = "Duplicate Detector"
    category = "calculation"
    description = "Detects exact and fuzzy duplicate invoices"
    
    input_schema = {
        "invoices": {"type": "array"}
    }
    
    output_schema = {
        "duplicates": {"type": "array", "description": "Groups of duplicate invoices"}
    }
    
    def run(self, input_data: List[Dict], params: Dict[str, Any] = None) -> Dict[str, List]:
        """
        Detect duplicates
        
        Rules from document:
        - Exact: Same Vendor + Same Invoice Number (100% confidence)
        - Fuzzy: Same Vendor + Same Amount + Same Date (75% confidence)
        
        Args:
            input_data: List of invoices
            params: tolerance for fuzzy matching
            
        Returns:
            Dict with exact_duplicates and fuzzy_duplicates
        """
        if not input_data:
            return {"exact_duplicates": [], "fuzzy_duplicates": []}
        
        params = params or {}
        tolerance = Decimal(str(params.get('tolerance', 0.01)))
        
        exact_duplicates = []
        fuzzy_duplicates = []
        
        # Build indices for matching
        exact_index = {}  # vendor + invoice_number
        fuzzy_index = {}  # vendor + amount + date
        
        for invoice in input_data:
            vendor = invoice.get('vendor_name') or invoice.get('vendor_id', '')
            invoice_number = invoice.get('document_number', '')
            amount = Decimal(str(invoice.get('inr_amount', 0)))
            invoice_date = invoice.get('document_date', '')
            
            # Exact duplicate detection (pure matching)
            exact_key = f"{vendor}||{invoice_number}"
            if exact_key in exact_index:
                # Found exact duplicate
                existing = exact_index[exact_key]
                exact_duplicates.append({
                    'group': [existing, invoice],
                    'confidence': 100,
                    'type': 'exact',
                    'reason': 'Same vendor and invoice number'
                })
            else:
                exact_index[exact_key] = invoice
            
            # Fuzzy duplicate detection (pure matching with tolerance)
            fuzzy_key = f"{vendor}||{invoice_date}"
            if fuzzy_key in fuzzy_index:
                # Check amount within tolerance
                for existing in fuzzy_index[fuzzy_key]:
                    existing_amount = Decimal(str(existing.get('inr_amount', 0)))
                    diff = abs(amount - existing_amount)
                    
                    if diff <= tolerance and invoice_number != existing.get('document_number', ''):
                        # Found fuzzy duplicate
                        fuzzy_duplicates.append({
                            'group': [existing, invoice],
                            'confidence': 75,
                            'type': 'fuzzy',
                            'reason': 'Same vendor, amount, and date but different invoice number'
                        })
                
                fuzzy_index[fuzzy_key].append(invoice)
            else:
                fuzzy_index[fuzzy_key] = [invoice]
        
        self.logger.info(
            f"Detected {len(exact_duplicates)} exact and "
            f"{len(fuzzy_duplicates)} fuzzy duplicates"
        )
        
        return {
            "exact_duplicates": exact_duplicates,
            "fuzzy_duplicates": fuzzy_duplicates
        }
@register_node
class DataTransformationNode(BaseNode):
    """
    Data Transformation Node
    Transforms invoice data from database format to Excel template format
    """
    
    name = "Data Transformer"
    category = "calculation"
    description = "Transforms database fields to Excel template format"
    
    input_schema = {
        "invoices": {"type": "array"}
    }
    
    output_schema = {
        "invoices": {"type": "array", "description": "Transformed invoices"}
    }
    
    def run(self, input_data: List[Dict], params: Dict[str, Any] = None) -> List[Dict]:
        """
        Transform invoice data for Excel template
        
        Maps transaction table fields to Excel template fields:
        - id -> trans_id
        - invoice_number -> invoice_no  (NEW: from vendor_invoices/customer_invoices)
        - invoice_date -> invoice_date  (already matches)
        - inr_amount -> invoice_amt     (NEW: converted amount from transaction tables)
        - tax_amount -> tax_amt         (NEW: from transaction tables)
        - total_amount -> raw amount    (NEW: original amount before conversion)
        
        Fallback to old field names for backward compatibility:
        - document_number -> invoice_no (OLD: from documents table)
        - grand_total -> invoice_amt    (OLD: from documents table)
        - tax_total -> tax_amt          (OLD: from documents table)
        """
        if not input_data:
            return []
        
        transformed = []
        
        for inv in input_data:
            # Handle both new (transaction tables) and old (documents table) field names
            # Priority: NEW transaction table fields first, then OLD documents table fields
            
            invoice_amt = float(
                inv.get('inr_amount') or           # NEW: from vendor_invoices/customer_invoices
                inv.get('total_amount') or         # NEW: original amount
                inv.get('grand_total') or          # OLD: from documents
                0
            )
            
            tax_amt = float(
                inv.get('tax_amount') or           # NEW: from transaction tables
                inv.get('tax_total') or            # OLD: from documents
                0
            )
            
            outstanding_amt = float(
                inv.get('outstanding_amount') or   # NEW: from transaction tables
                inv.get('outstanding') or          # OLD: from documents
                0
            )
            
            paid_amt = float(
                inv.get('paid_amount') or          # NEW: from vendor_invoices
                inv.get('received_amount') or      # NEW: from customer_invoices
                0
            )
            
            # If paid_amt not in database, calculate from invoice_amt - outstanding
            if paid_amt == 0 and outstanding_amt > 0:
                paid_amt = invoice_amt - outstanding_amt
            
            # According to requirement: invoice_amt should be net amount (subtotal), net_amt should be invoice amount (total)
            net_amt = invoice_amt  # Invoice amount (total including tax)
            invoice_amt = invoice_amt - tax_amt  # Net amount (subtotal excluding tax)
            
            # Determine status
            if outstanding_amt <= 0 or paid_amt >= invoice_amt:
                status = 'Paid'
            elif paid_amt > 0:
                status = 'Partial'
            else:
                status = 'Unpaid'
            
            # Get description
            description = inv.get('description', '')
            if not description and inv.get('original_currency') != 'INR':
                # Show original currency if converted
                orig_curr = inv.get('original_currency', 'INR')
                total_amt = inv.get('total_amount', invoice_amt)
                description = f"{orig_curr} {total_amt:.2f}"
            
            transformed_inv = {
                'trans_id': inv.get('id', ''),
                'vendor_name': inv.get('vendor_name', inv.get('customer_name', '')),
                'vendor_id': inv.get('vendor_id', inv.get('customer_id', '')),
                'customer_name': inv.get('customer_name', inv.get('vendor_name', '')),
                'customer_id': inv.get('customer_id', inv.get('vendor_id', '')),
                # Support both new and old field names for invoice number
                'invoice_no': (
                    inv.get('invoice_number') or      # NEW: from transaction tables
                    inv.get('document_number') or     # OLD: from documents
                    ''
                ),
                # invoice_date already matches in both schemas
                'invoice_date': inv.get('invoice_date', ''),
                'due_date': inv.get('due_date', ''),
                'description': description or 'General Invoice',
                'net_amt': invoice_amt,  # Net amount (subtotal excluding tax)
                'tax_amt': tax_amt,
                'sub_total': net_amt,    # Sub total (total including tax)
                'paid_amt': paid_amt,
                'outstanding': outstanding_amt,  
                'status': status
            }
            
            transformed.append(transformed_inv)
        
        return transformed