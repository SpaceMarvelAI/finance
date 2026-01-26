"""
Canonical Financial Schema
Universal data structure for all financial documents
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Supported document types"""
    VENDOR_INVOICE = "vendor_invoice"
    CUSTOMER_INVOICE = "customer_invoice"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"
    BANK_STATEMENT = "bank_statement"
    EXPENSE_BILL = "expense_bill"
    PURCHASE_ORDER = "purchase_order"
    SALES_ORDER = "sales_order"
    FINANCIAL_STATEMENT = "financial_statement"
    MIS_REPORT = "mis_report"
    TRANSACTION_LIST = "transaction_list"


class Currency(str, Enum):
    """Supported currencies"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    INR = "INR"
    JPY = "JPY"


class DocumentMetadata(BaseModel):
    """Document metadata"""
    document_number: Optional[str] = None
    document_date: Optional[str] = None
    due_date: Optional[str] = None
    currency: Currency = Currency.USD
    document_type: DocumentType = DocumentType.VENDOR_INVOICE
    source_file: Optional[str] = None
    ingestion_date: Optional[str] = None
    company_id: Optional[str] = None


class Entity(BaseModel):
    """Represents a business entity (vendor/customer)"""
    name: Optional[str] = None
    tax_id: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    account_number: Optional[str] = None


class LineItem(BaseModel):
    """Individual line item in invoice/order"""
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    line_total: Optional[float] = None
    tax_rate: Optional[float] = None
    tax_amount: Optional[float] = None
    hsn_code: Optional[str] = None  # For Indian tax system


class TaxBreakdown(BaseModel):
    """Tax breakdown for invoices"""
    cgst: Optional[float] = None  # Central GST (India)
    sgst: Optional[float] = None  # State GST (India)
    igst: Optional[float] = None  # Integrated GST (India)
    vat: Optional[float] = None   # VAT (other countries)
    sales_tax: Optional[float] = None


class Totals(BaseModel):
    """Financial totals"""
    subtotal: float = 0.0
    tax_total: float = 0.0
    discount: float = 0.0
    grand_total: float = 0.0
    amount_paid: float = 0.0
    balance_due: float = 0.0


class BankTransaction(BaseModel):
    """Bank statement transaction"""
    transaction_date: Optional[str] = None
    description: Optional[str] = None
    debit: Optional[float] = None
    credit: Optional[float] = None
    balance: Optional[float] = None
    reference_number: Optional[str] = None
    category: Optional[str] = None


class AuditTrail(BaseModel):
    """Audit and validation information"""
    extraction_confidence: Optional[float] = None
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)
    processing_notes: List[str] = Field(default_factory=list)
    extracted_by: str = "system"
    validated_by: Optional[str] = None


class CanonicalFinancialDocument(BaseModel):
    """
    Universal canonical schema for all financial documents
    This is the single source of truth for all extracted data
    """
    
    # Core metadata
    document_metadata: DocumentMetadata
    
    # Parties involved
    seller: Optional[Entity] = None
    buyer: Optional[Entity] = None
    vendor: Optional[Entity] = None  # For AP
    customer: Optional[Entity] = None  # For AR
    
    # Line items
    line_items: List[LineItem] = Field(default_factory=list)
    
    # Financial totals
    totals: Totals = Field(default_factory=Totals)
    
    # Tax breakdown
    tax_breakdown: Optional[TaxBreakdown] = None
    
    # Bank transactions (for bank statements)
    bank_transactions: List[BankTransaction] = Field(default_factory=list)
    
    # Purchase/Sales order references
    po_reference: Optional[str] = None
    so_reference: Optional[str] = None
    
    # Payment terms
    payment_terms: Optional[str] = None
    payment_method: Optional[str] = None
    
    # Additional fields for flexibility
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    
    # Audit trail
    audit: AuditTrail = Field(default_factory=AuditTrail)
    
    class Config:
        use_enum_values = True


class CompanyProfile(BaseModel):
    """Company/tenant profile"""
    company_id: str
    company_name: str
    tax_id: str
    logo_url: Optional[str] = None
    primary_color: str = "#1976D2"
    secondary_color: str = "#424242"
    currency: Currency = Currency.USD
    fiscal_year_start: str = "01-01"  # MM-DD format
    
    # Master data
    vendor_master: Dict[str, Entity] = Field(default_factory=dict)
    customer_master: Dict[str, Entity] = Field(default_factory=dict)
    chart_of_accounts: Dict[str, str] = Field(default_factory=dict)


# Canonical schema template (for backward compatibility)
CANONICAL_SCHEMA_TEMPLATE = {
    "document_metadata": {
        "document_number": None,
        "document_date": None,
        "due_date": None,
        "currency": "USD",
        "document_type": "vendor_invoice",
        "source_file": None,
        "ingestion_date": None
    },
    "seller": {
        "name": None,
        "tax_id": None,
        "address": None,
        "email": None
    },
    "buyer": {
        "name": None,
        "tax_id": None,
        "address": None,
        "email": None
    },
    "line_items": [],
    "totals": {
        "subtotal": 0.0,
        "tax_total": 0.0,
        "grand_total": 0.0,
        "balance_due": 0.0
    },
    "tax_breakdown": {
        "cgst": None,
        "sgst": None,
        "igst": None
    },
    "audit": {
        "extraction_confidence": None,
        "validation_errors": [],
        "validation_warnings": []
    }
}