"""
Financial Calculation Engine
Pure Python calculations - NO LLM
Handles all financial formulas, categorization, and computations
"""

from typing import Dict, List, Any
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from enum import Enum

from data_layer.schemas.canonical_schema import (
    CanonicalFinancialDocument,
    LineItem,
    Totals,
    DocumentType
)
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class InvoiceCategory(Enum):
    """Invoice categories for classification"""
    SALES = "sales"           # Customer invoices (AR)
    PURCHASE = "purchase"     # Vendor invoices (AP)
    EXPENSE = "expense"       # Expense bills
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"
    PROFORMA = "proforma"


class CalculationEngine:
    """
    Financial calculation engine
    All calculations done in Python - NO LLM calls
    """
    
    def __init__(self):
        self.logger = logger
        self.precision = Decimal('0.01')  # 2 decimal places
    
    def categorize_document(self, doc: CanonicalFinancialDocument) -> InvoiceCategory:
        """
        Categorize document based on type and content
        
        Args:
            doc: Canonical financial document
            
        Returns:
            Invoice category
        """
        doc_type = doc.document_metadata.document_type
        
        # Check document type
        if doc_type == DocumentType.CUSTOMER_INVOICE:
            return InvoiceCategory.SALES
        elif doc_type == DocumentType.VENDOR_INVOICE:
            return InvoiceCategory.PURCHASE
        elif doc_type == DocumentType.CREDIT_NOTE:
            return InvoiceCategory.CREDIT_NOTE
        elif doc_type == DocumentType.DEBIT_NOTE:
            return InvoiceCategory.DEBIT_NOTE
        
        # Check based on seller/buyer presence
        if doc.seller and not doc.buyer:
            # Has seller, no buyer = vendor invoice (we're buying)
            return InvoiceCategory.PURCHASE
        elif doc.buyer and not doc.seller:
            # Has buyer, no seller = customer invoice (we're selling)
            return InvoiceCategory.SALES
        
        # Default to purchase for vendor invoices
        return InvoiceCategory.PURCHASE
    
    def calculate_line_totals(self, doc: CanonicalFinancialDocument) -> CanonicalFinancialDocument:
        """
        Calculate/validate line item totals
        
        Formula: line_total = quantity × unit_price
        """
        for item in doc.line_items:
            if item.quantity and item.unit_price:
                calculated_total = self._to_decimal(item.quantity) * self._to_decimal(item.unit_price)
                
                if item.line_total:
                    # Validate existing total
                    diff = abs(calculated_total - self._to_decimal(item.line_total))
                    if diff > Decimal('0.02'):  # Allow 2 cent rounding difference
                        self.logger.warning(
                            f"Line total mismatch: {item.description} "
                            f"calculated={calculated_total}, provided={item.line_total}"
                        )
                else:
                    # Set calculated total
                    item.line_total = float(calculated_total)
        
        return doc
    
    def calculate_document_totals(self, doc: CanonicalFinancialDocument) -> CanonicalFinancialDocument:
        """
        Calculate document totals from line items
        
        Formulas:
        - subtotal = sum(line_items.line_total)
        - tax_total = sum(line_items.tax_amount) OR (subtotal × avg_tax_rate)
        - grand_total = subtotal + tax_total - discount
        - balance_due = grand_total - amount_paid
        """
        # Calculate subtotal from line items
        subtotal = sum(
            self._to_decimal(item.line_total or 0)
            for item in doc.line_items
        )
        
        # Calculate tax total
        tax_total = Decimal('0')
        
        # Method 1: Sum tax amounts from line items
        if any(item.tax_amount for item in doc.line_items):
            tax_total = sum(
                self._to_decimal(item.tax_amount or 0)
                for item in doc.line_items
            )
        # Method 2: Calculate from tax rates
        elif any(item.tax_rate for item in doc.line_items):
            for item in doc.line_items:
                if item.tax_rate and item.line_total:
                    item_tax = self._to_decimal(item.line_total) * (self._to_decimal(item.tax_rate) / 100)
                    tax_total += item_tax
        # Method 3: Use provided tax breakdown
        elif doc.tax_breakdown:
            tax_total = sum([
                self._to_decimal(doc.tax_breakdown.cgst or 0),
                self._to_decimal(doc.tax_breakdown.sgst or 0),
                self._to_decimal(doc.tax_breakdown.igst or 0),
                self._to_decimal(doc.tax_breakdown.vat or 0)
            ])
        
        # Get discount
        discount = self._to_decimal(doc.totals.discount or 0)
        
        # Calculate grand total
        grand_total = subtotal + tax_total - discount
        
        # Calculate balance due
        amount_paid = self._to_decimal(doc.totals.amount_paid or 0)
        balance_due = grand_total - amount_paid
        
        # Update document totals
        doc.totals.subtotal = float(subtotal)
        doc.totals.tax_total = float(tax_total)
        doc.totals.grand_total = float(grand_total)
        doc.totals.balance_due = float(balance_due)
        
        # Validate against provided grand_total if exists
        if doc.totals.grand_total and abs(grand_total - self._to_decimal(doc.totals.grand_total)) > Decimal('0.10'):
            self.logger.warning(
                f"Grand total mismatch: calculated={grand_total}, "
                f"provided={doc.totals.grand_total}"
            )
        
        return doc
    
    def calculate_aging(self, doc: CanonicalFinancialDocument, as_of_date: datetime = None) -> Dict[str, Any]:
        """
        Calculate accounts aging buckets
        
        Returns:
            Aging analysis: current, 0-30, 31-60, 61-90, 90+
        """
        if not as_of_date:
            as_of_date = datetime.now()
        
        # Get due date
        due_date_str = doc.document_metadata.due_date
        if not due_date_str:
            # Estimate due date from document date + payment terms
            doc_date_str = doc.document_metadata.document_date
            if doc_date_str:
                try:
                    doc_date = datetime.fromisoformat(doc_date_str)
                    # Default 30 days
                    due_date = doc_date + timedelta(days=30)
                except:
                    due_date = as_of_date
            else:
                due_date = as_of_date
        else:
            try:
                due_date = datetime.fromisoformat(due_date_str)
            except:
                due_date = as_of_date
        
        # Calculate days overdue
        days_overdue = (as_of_date - due_date).days
        
        # Determine aging bucket
        bucket = "current"
        if days_overdue > 0:
            if days_overdue <= 30:
                bucket = "0-30"
            elif days_overdue <= 60:
                bucket = "31-60"
            elif days_overdue <= 90:
                bucket = "61-90"
            else:
                bucket = "90+"
        
        return {
            "document_number": doc.document_metadata.document_number,
            "due_date": due_date.isoformat(),
            "days_overdue": max(0, days_overdue),
            "aging_bucket": bucket,
            "balance_due": doc.totals.balance_due,
            "category": self.categorize_document(doc).value
        }
    
    def calculate_tax_breakdown(self, doc: CanonicalFinancialDocument) -> Dict[str, float]:
        """
        Calculate tax breakdown (GST/VAT)
        
        Returns:
            Tax components with amounts
        """
        tax_breakdown = {}
        
        if doc.tax_breakdown:
            tax_breakdown = {
                "cgst": float(doc.tax_breakdown.cgst or 0),
                "sgst": float(doc.tax_breakdown.sgst or 0),
                "igst": float(doc.tax_breakdown.igst or 0),
                "vat": float(doc.tax_breakdown.vat or 0)
            }
        else:
            # Try to calculate from line items
            total_tax = self._to_decimal(doc.totals.tax_total or 0)
            
            # For Indian invoices, split equally between CGST and SGST
            if total_tax > 0:
                tax_breakdown = {
                    "cgst": float(total_tax / 2),
                    "sgst": float(total_tax / 2),
                    "igst": 0.0,
                    "vat": 0.0
                }
        
        return tax_breakdown
    
    def validate_calculations(self, doc: CanonicalFinancialDocument) -> Dict[str, Any]:
        """
        Validate all calculations and return issues
        
        Returns:
            Validation results with errors and warnings
        """
        errors = []
        warnings = []
        
        # Validate line totals
        for i, item in enumerate(doc.line_items):
            if item.quantity and item.unit_price and item.line_total:
                calculated = float(self._to_decimal(item.quantity) * self._to_decimal(item.unit_price))
                diff = abs(calculated - item.line_total)
                
                if diff > 0.10:
                    errors.append(
                        f"Line {i+1}: Total mismatch (calc={calculated:.2f}, "
                        f"provided={item.line_total:.2f})"
                    )
        
        # Validate document total
        calculated_subtotal = sum(
            self._to_decimal(item.line_total or 0)
            for item in doc.line_items
        )
        
        if doc.totals.subtotal:
            diff = abs(calculated_subtotal - self._to_decimal(doc.totals.subtotal))
            if diff > 0.10:
                warnings.append(
                    f"Subtotal mismatch (calc={calculated_subtotal:.2f}, "
                    f"provided={doc.totals.subtotal:.2f})"
                )
        
        # Validate grand total formula
        if doc.totals.subtotal and doc.totals.tax_total:
            calculated_grand = (
                self._to_decimal(doc.totals.subtotal) +
                self._to_decimal(doc.totals.tax_total) -
                self._to_decimal(doc.totals.discount or 0)
            )
            
            if doc.totals.grand_total:
                diff = abs(calculated_grand - self._to_decimal(doc.totals.grand_total))
                if diff > 0.10:
                    errors.append(
                        f"Grand total mismatch (calc={calculated_grand:.2f}, "
                        f"provided={doc.totals.grand_total:.2f})"
                    )
        
        is_valid = len(errors) == 0
        
        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "confidence": 1.0 if is_valid else 0.5
        }
    
    def _to_decimal(self, value: Any) -> Decimal:
        """Convert value to Decimal for precise calculations"""
        if value is None:
            return Decimal('0')
        
        try:
            return Decimal(str(value)).quantize(self.precision, rounding=ROUND_HALF_UP)
        except:
            return Decimal('0')