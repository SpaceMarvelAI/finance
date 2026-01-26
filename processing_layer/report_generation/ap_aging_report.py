"""
AP AGING REPORT - CORRECTED VERSION
- Uses database for INR amounts
- Returns correct structure with 'table_data' and 'headers'
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, date
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class APAgingReportGenerator:
    """
    AP Aging Report Generator
    
    Shows how long invoices have been pending in aging buckets
    """
    
    def __init__(self, mcp_tools=None):
        """Initialize with database access"""
        self.mcp_tools = mcp_tools
        
        # Import database manager
        from data_layer.database.database_manager import get_database
        self.db = get_database()
        
        self.logger = logger
        self.logger.info("APAgingReportGenerator initialized with database access")
    
    def generate_report(self, as_of_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate AP Aging Report
        
        Args:
            as_of_date: Date for aging calculation (default: today)
            
        Returns:
            Report data with table_data structure
        """
        
        # Parse as_of_date
        if as_of_date:
            try:
                current_date = datetime.fromisoformat(as_of_date.replace('Z', '+00:00')).date()
            except:
                current_date = date.today()
        else:
            current_date = date.today()
        
        # Get purchase invoices from database
        try:
            purchase_docs = self.db.get_documents_by_category('purchase', None)
            self.logger.info(f"Retrieved {len(purchase_docs)} purchase documents from database")
        except Exception as e:
            self.logger.error(f"Database error: {e}")
            purchase_docs = []
        
        vendor_invoice_rows = []
        grand_totals = {
            "total_due": 0.0,
            "current_0_30": 0.0,
            "days_31_60": 0.0,
            "days_61_90": 0.0,
            "days_90_plus": 0.0
        }
        
        for doc_entry in purchase_docs:
            # Get amounts from database (already in INR)
            invoice_amount = float(doc_entry.get("grand_total") or 0)  # FIX: Use grand_total instead of inr_amount
            paid_amount = float(doc_entry.get("paid_amount") or 0)
            
            # Calculate outstanding
            total_due = invoice_amount - paid_amount
            
            # Skip if fully paid
            if total_due <= 0:
                continue
            
            # Get fields
            vendor_name = doc_entry.get("vendor_name") or "Unknown Vendor"
            invoice_no = doc_entry.get("document_number") or "N/A"
            due_date_str = doc_entry.get("document_date")
            
            # Parse due date
            due_date = self._parse_date(due_date_str)
            
            # Calculate overdue days
            if due_date:
                overdue_days = (current_date - due_date).days
            else:
                overdue_days = 0
            
            # Distribute into aging buckets
            current_0_30 = 0.0
            days_31_60 = 0.0
            days_61_90 = 0.0
            days_90_plus = 0.0
            
            if overdue_days <= 30:
                current_0_30 = total_due
            elif overdue_days <= 60:
                days_31_60 = total_due
            elif overdue_days <= 90:
                days_61_90 = total_due
            else:
                days_90_plus = total_due
            
            # Create row
            row = {
                "vendor_name": vendor_name,
                "invoice_no": invoice_no,
                "due_date": due_date.strftime("%m/%d/%y") if due_date else "",
                "total_due": round(total_due, 2),
                "current_0_30": round(current_0_30, 2),
                "days_31_60": round(days_31_60, 2),
                "days_61_90": round(days_61_90, 2),
                "days_90_plus": round(days_90_plus, 2)
            }
            
            vendor_invoice_rows.append(row)
            
            # Update grand totals
            grand_totals["total_due"] += total_due
            grand_totals["current_0_30"] += current_0_30
            grand_totals["days_31_60"] += days_31_60
            grand_totals["days_61_90"] += days_61_90
            grand_totals["days_90_plus"] += days_90_plus
        
        # Round grand totals
        for key in grand_totals:
            grand_totals[key] = round(grand_totals[key], 2)
        
        self.logger.info(f"Generated aging report: {len(vendor_invoice_rows)} unpaid invoices, total due: ₹{grand_totals['total_due']:,.2f}")
        
        # Return with CORRECT structure (table_data with headers)
        return {
            "report_metadata": {
                "report_type": "AP_AGING",
                "report_name": "AP Aging Report",
                "as_of_date": current_date.isoformat(),
                "generated_at": datetime.now().isoformat(),
                "currency": "INR"
            },
            "table_data": {
                "headers": [
                    "Vendor Name", "Invoice No.", "Due Date", "Total Due",
                    "Current (0-30)", "31-60 Days", "61-90 Days", "90+ Days"
                ],
                "rows": vendor_invoice_rows,
                "grand_totals": grand_totals
            },
            "summary": {
                "total_vendors": len(set(row["vendor_name"] for row in vendor_invoice_rows)),
                "total_invoices": len(vendor_invoice_rows),
                "total_amount_due": grand_totals["total_due"]
            }
        }
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object"""
        if not date_str:
            return None
        
        try:
            # Try ISO format
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.date()
        except:
            try:
                # Try other formats
                for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m/%d/%y"]:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        return dt.date()
                    except:
                        continue
            except:
                pass
        
        return None