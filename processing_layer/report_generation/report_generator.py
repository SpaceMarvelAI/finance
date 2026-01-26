"""
Report Generator - Structured Output
Returns data in proper table format for report generation
"""

from typing import Dict, Any, List
from datetime import datetime
from decimal import Decimal

from shared.tools.mcp_financial_tools import PersistentFinancialMCPTools
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class ReportGenerator:
    """
    Report Generator - Structured Data Output
    
    Returns data in proper table format ready for:
    - Excel generation
    - PDF generation
    - Chart/graph rendering
    - API response
    
    NO verbose text - ONLY structured data!
    """
    
    def __init__(self, mcp_tools: FinancialMCPTools = None):
        self.mcp_tools = mcp_tools or FinancialMCPTools()
        self.logger = logger
    
    def generate_ar_aging_report(self) -> Dict[str, Any]:
        """
        Generate AR Aging Report - Structured Format
        
        Returns:
            {
                "report_metadata": {...},
                "summary": {...},
                "aging_buckets": [...],
                "details": [...]
            }
        """
        
        # Get data from MCP tools
        ar_aging = self.mcp_tools.get_ar_aging_report()
        
        # Structure for report generation
        report = {
            "report_metadata": {
                "report_type": "AR_AGING",
                "report_name": "Accounts Receivable Aging Report",
                "generated_at": datetime.now().isoformat(),
                "as_of_date": ar_aging["as_of_date"],
                "currency": "USD"
            },
            
            "summary": {
                "total_receivables": ar_aging["totals"]["total"],
                "current": ar_aging["totals"]["current"],
                "overdue_0_30": ar_aging["totals"]["0-30"],
                "overdue_31_60": ar_aging["totals"]["31-60"],
                "overdue_61_90": ar_aging["totals"]["61-90"],
                "overdue_90_plus": ar_aging["totals"]["90+"],
                "total_overdue": (
                    ar_aging["totals"]["0-30"] +
                    ar_aging["totals"]["31-60"] +
                    ar_aging["totals"]["61-90"] +
                    ar_aging["totals"]["90+"]
                ),
                "document_count": ar_aging["document_count"]
            },
            
            "aging_buckets": [
                {
                    "bucket": "Current",
                    "days": "0",
                    "amount": ar_aging["totals"]["current"],
                    "count": len(ar_aging["aging_buckets"]["current"]),
                    "percentage": self._calculate_percentage(
                        ar_aging["totals"]["current"],
                        ar_aging["totals"]["total"]
                    )
                },
                {
                    "bucket": "0-30 Days",
                    "days": "1-30",
                    "amount": ar_aging["totals"]["0-30"],
                    "count": len(ar_aging["aging_buckets"]["0-30"]),
                    "percentage": self._calculate_percentage(
                        ar_aging["totals"]["0-30"],
                        ar_aging["totals"]["total"]
                    )
                },
                {
                    "bucket": "31-60 Days",
                    "days": "31-60",
                    "amount": ar_aging["totals"]["31-60"],
                    "count": len(ar_aging["aging_buckets"]["31-60"]),
                    "percentage": self._calculate_percentage(
                        ar_aging["totals"]["31-60"],
                        ar_aging["totals"]["total"]
                    )
                },
                {
                    "bucket": "61-90 Days",
                    "days": "61-90",
                    "amount": ar_aging["totals"]["61-90"],
                    "count": len(ar_aging["aging_buckets"]["61-90"]),
                    "percentage": self._calculate_percentage(
                        ar_aging["totals"]["61-90"],
                        ar_aging["totals"]["total"]
                    )
                },
                {
                    "bucket": "90+ Days",
                    "days": ">90",
                    "amount": ar_aging["totals"]["90+"],
                    "count": len(ar_aging["aging_buckets"]["90+"]),
                    "percentage": self._calculate_percentage(
                        ar_aging["totals"]["90+"],
                        ar_aging["totals"]["total"]
                    )
                }
            ],
            
            "details": self._flatten_aging_details(ar_aging["aging_buckets"])
        }
        
        return report
    
    def generate_ap_aging_report(self) -> Dict[str, Any]:
        """Generate AP Aging Report - Structured Format"""
        
        ap_aging = self.mcp_tools.get_ap_aging_report()
        
        report = {
            "report_metadata": {
                "report_type": "AP_AGING",
                "report_name": "Accounts Payable Aging Report",
                "generated_at": datetime.now().isoformat(),
                "as_of_date": ap_aging["as_of_date"],
                "currency": "USD"
            },
            
            "summary": {
                "total_payables": ap_aging["totals"]["total"],
                "current": ap_aging["totals"]["current"],
                "overdue_0_30": ap_aging["totals"]["0-30"],
                "overdue_31_60": ap_aging["totals"]["31-60"],
                "overdue_61_90": ap_aging["totals"]["61-90"],
                "overdue_90_plus": ap_aging["totals"]["90+"],
                "total_overdue": (
                    ap_aging["totals"]["0-30"] +
                    ap_aging["totals"]["31-60"] +
                    ap_aging["totals"]["61-90"] +
                    ap_aging["totals"]["90+"]
                ),
                "document_count": ap_aging["document_count"]
            },
            
            "aging_buckets": [
                {
                    "bucket": "Current",
                    "days": "0",
                    "amount": ap_aging["totals"]["current"],
                    "count": len(ap_aging["aging_buckets"]["current"]),
                    "percentage": self._calculate_percentage(
                        ap_aging["totals"]["current"],
                        ap_aging["totals"]["total"]
                    )
                },
                {
                    "bucket": "0-30 Days",
                    "days": "1-30",
                    "amount": ap_aging["totals"]["0-30"],
                    "count": len(ap_aging["aging_buckets"]["0-30"]),
                    "percentage": self._calculate_percentage(
                        ap_aging["totals"]["0-30"],
                        ap_aging["totals"]["total"]
                    )
                },
                {
                    "bucket": "31-60 Days",
                    "days": "31-60",
                    "amount": ap_aging["totals"]["31-60"],
                    "count": len(ap_aging["aging_buckets"]["31-60"]),
                    "percentage": self._calculate_percentage(
                        ap_aging["totals"]["31-60"],
                        ap_aging["totals"]["total"]
                    )
                },
                {
                    "bucket": "61-90 Days",
                    "days": "61-90",
                    "amount": ap_aging["totals"]["61-90"],
                    "count": len(ap_aging["aging_buckets"]["61-90"]),
                    "percentage": self._calculate_percentage(
                        ap_aging["totals"]["61-90"],
                        ap_aging["totals"]["total"]
                    )
                },
                {
                    "bucket": "90+ Days",
                    "days": ">90",
                    "amount": ap_aging["totals"]["90+"],
                    "count": len(ap_aging["aging_buckets"]["90+"]),
                    "percentage": self._calculate_percentage(
                        ap_aging["totals"]["90+"],
                        ap_aging["totals"]["total"]
                    )
                }
            ],
            
            "details": self._flatten_aging_details(ap_aging["aging_buckets"])
        }
        
        return report
    
    def generate_profit_loss_report(
        self,
        start_date: str = None,
        end_date: str = None
    ) -> Dict[str, Any]:
        """Generate P&L Report - Structured Format"""
        
        pl_data = self.mcp_tools.get_profit_loss_statement(start_date, end_date)
        
        report = {
            "report_metadata": {
                "report_type": "PROFIT_LOSS",
                "report_name": "Profit & Loss Statement",
                "generated_at": datetime.now().isoformat(),
                "period_start": pl_data["period"]["start_date"],
                "period_end": pl_data["period"]["end_date"],
                "currency": "USD"
            },
            
            "summary": {
                "revenue": pl_data["revenue"],
                "expenses": pl_data["expenses"],
                "gross_profit": pl_data["gross_profit"],
                "profit_margin": pl_data["profit_margin"]
            },
            
            "revenue_breakdown": [
                {
                    "category": "Sales",
                    "amount": pl_data["revenue"],
                    "document_count": pl_data["document_counts"]["sales"]
                }
            ],
            
            "expense_breakdown": [
                {
                    "category": "Purchases",
                    "amount": pl_data["expenses"],
                    "document_count": pl_data["document_counts"]["purchases"]
                }
            ]
        }
        
        return report
    
    def generate_vendor_summary_report(
        self,
        vendor_name: str = None
    ) -> Dict[str, Any]:
        """Generate Vendor Summary - Structured Format"""
        
        vendor_data = self.mcp_tools.get_vendor_summary(vendor_name)
        
        # Convert to list format
        vendors_list = []
        for vendor, data in vendor_data["vendors"].items():
            vendors_list.append({
                "vendor_name": vendor,
                "invoice_count": data["invoice_count"],
                "total_amount": data["total_amount"],
                "balance_due": data["balance_due"],
                "paid_amount": data["total_amount"] - data["balance_due"]
            })
        
        report = {
            "report_metadata": {
                "report_type": "VENDOR_SUMMARY",
                "report_name": "Vendor Purchase Summary",
                "generated_at": datetime.now().isoformat(),
                "vendor_filter": vendor_data["vendor_filter"],
                "currency": "USD"
            },
            
            "summary": {
                "total_vendors": vendor_data["total_vendors"],
                "total_purchase_amount": sum(v["total_amount"] for v in vendors_list),
                "total_balance_due": sum(v["balance_due"] for v in vendors_list),
                "total_invoices": sum(v["invoice_count"] for v in vendors_list)
            },
            
            "vendors": vendors_list
        }
        
        return report
    
    def _flatten_aging_details(self, aging_buckets: Dict) -> List[Dict]:
        """Flatten aging buckets into detail rows"""
        
        details = []
        
        for bucket_name, invoices in aging_buckets.items():
            for invoice in invoices:
                details.append({
                    "document_number": invoice.get("document_number"),
                    "vendor": invoice.get("vendor", "N/A"),
                    "due_date": invoice.get("due_date"),
                    "days_overdue": invoice.get("days_overdue", 0),
                    "amount": invoice.get("balance"),
                    "aging_bucket": bucket_name
                })
        
        return details
    
    def _calculate_percentage(self, amount: float, total: float) -> float:
        """Calculate percentage"""
        if total == 0:
            return 0.0
        return round((amount / total) * 100, 2)