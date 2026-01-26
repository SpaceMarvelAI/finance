"""
Enhanced Database Schema for Financial Automation System
Handles all document types with intelligent extraction
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey, Boolean, Enum, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum


Base = declarative_base()


# ============================================================================
# ENUMS
# ============================================================================

class DocumentType(enum.Enum):
    """All supported document types"""
    VENDOR_INVOICE = "vendor_invoice"
    CUSTOMER_INVOICE = "customer_invoice"
    PURCHASE_ORDER = "purchase_order"
    SALES_ORDER = "sales_order"
    BANK_STATEMENT = "bank_statement"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"
    EXPENSE_BILL = "expense_bill"
    RECEIPT = "receipt"
    PAYMENT_VOUCHER = "payment_voucher"
    JOURNAL_ENTRY = "journal_entry"


class ProcessingStatus(enum.Enum):
    """Document processing status"""
    PENDING = "pending"
    PARSING = "parsing"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


class PaymentStatus(enum.Enum):
    """Payment status for invoices"""
    UNPAID = "unpaid"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"


# ============================================================================
# MASTER DATA TABLES
# ============================================================================

class Company(Base):
    """Company/Tenant master data"""
    __tablename__ = "companies"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    tax_id = Column(String(50))
    registration_number = Column(String(50))
    
    # Contact info
    email = Column(String(255))
    phone = Column(String(50))
    website = Column(String(255))
    
    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    # Branding
    logo_url = Column(String(500))
    primary_color = Column(String(7), default="#1976D2")
    secondary_color = Column(String(7), default="#424242")
    
    # Settings
    currency = Column(String(3), default="USD")
    fiscal_year_start = Column(String(5))  # MM-DD
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = relationship("Document", back_populates="company")
    vendors = relationship("Vendor", back_populates="company")
    customers = relationship("Customer", back_populates="company")
    bank_accounts = relationship("BankAccount", back_populates="company")


class Vendor(Base):
    """Vendor master data"""
    __tablename__ = "vendors"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    
    # Basic info
    vendor_code = Column(String(50), unique=True)
    vendor_name = Column(String(255), nullable=False)
    tax_id = Column(String(50))
    
    # Contact
    contact_person = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    
    # Address
    address_line1 = Column(String(255))
    city = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    # Payment terms
    payment_terms_days = Column(Integer, default=30)
    currency = Column(String(3), default="USD")
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    tags = Column(JSON)  # ["supplier", "recurring", etc.]
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="vendors")
    invoices = relationship("VendorInvoice", back_populates="vendor")


class Customer(Base):
    """Customer master data"""
    __tablename__ = "customers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    
    # Basic info
    customer_code = Column(String(50), unique=True)
    customer_name = Column(String(255), nullable=False)
    tax_id = Column(String(50))
    
    # Contact
    contact_person = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    
    # Address
    address_line1 = Column(String(255))
    city = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    # Payment terms
    payment_terms_days = Column(Integer, default=30)
    credit_limit = Column(Numeric(15, 2))
    currency = Column(String(3), default="USD")
    
    # Status
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="customers")
    invoices = relationship("CustomerInvoice", back_populates="customer")


class BankAccount(Base):
    """Bank account master data"""
    __tablename__ = "bank_accounts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    
    account_name = Column(String(255), nullable=False)
    bank_name = Column(String(255))
    account_number = Column(String(100))
    routing_number = Column(String(50))
    swift_code = Column(String(50))
    currency = Column(String(3), default="USD")
    
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="bank_accounts")
    transactions = relationship("BankTransaction", back_populates="bank_account")


# ============================================================================
# DOCUMENT STORAGE
# ============================================================================

class Document(Base):
    """Universal document storage with parsed data"""
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    
    # File info
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500))
    file_type = Column(String(10))  # pdf, xlsx, csv, docx
    file_size = Column(Integer)
    
    # Document classification
    document_type = Column(Enum(DocumentType), nullable=False)
    document_number = Column(String(100))
    document_date = Column(DateTime)
    
    # Docling parsed data (full parsed output)
    docling_parsed_data = Column(JSON)  # Complete Docling output
    
    # Canonical extracted data (structured)
    canonical_data = Column(JSON)  # Extracted financial data
    
    # Processing status
    status = Column(Enum(ProcessingStatus), default=ProcessingStatus.PENDING)
    processing_errors = Column(JSON)  # List of errors
    confidence_score = Column(Float)  # Extraction confidence 0-1
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    parsed_at = Column(DateTime)
    processed_at = Column(DateTime)
    
    # Relationships
    company = relationship("Company", back_populates="documents")


# ============================================================================
# TRANSACTION TABLES
# ============================================================================

class VendorInvoice(Base):
    """Vendor/Purchase invoices (AP)"""
    __tablename__ = "vendor_invoices"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    vendor_id = Column(String(36), ForeignKey("vendors.id"))
    document_id = Column(String(36), ForeignKey("documents.id"))  # Link to source doc
    
    # Invoice details
    invoice_number = Column(String(100), nullable=False)
    invoice_date = Column(DateTime)
    due_date = Column(DateTime)
    
    # Amounts
    subtotal = Column(Numeric(15, 2))
    tax_amount = Column(Numeric(15, 2))
    total_amount = Column(Numeric(15, 2), nullable=False)
    paid_amount = Column(Numeric(15, 2), default=0)
    outstanding_amount = Column(Numeric(15, 2))
    
    # Status
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.UNPAID)
    
    # Line items (JSON)
    line_items = Column(JSON)  # [{description, qty, rate, amount}]
    
    # Metadata
    currency = Column(String(3), default="USD")
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vendor = relationship("Vendor", back_populates="invoices")


class CustomerInvoice(Base):
    """Customer/Sales invoices (AR)"""
    __tablename__ = "customer_invoices"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    customer_id = Column(String(36), ForeignKey("customers.id"))
    document_id = Column(String(36), ForeignKey("documents.id"))
    
    # Invoice details
    invoice_number = Column(String(100), nullable=False)
    invoice_date = Column(DateTime)
    due_date = Column(DateTime)
    
    # Amounts
    subtotal = Column(Numeric(15, 2))
    tax_amount = Column(Numeric(15, 2))
    total_amount = Column(Numeric(15, 2), nullable=False)
    paid_amount = Column(Numeric(15, 2), default=0)
    outstanding_amount = Column(Numeric(15, 2))
    
    # Status
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.UNPAID)
    
    # Line items
    line_items = Column(JSON)
    
    currency = Column(String(3), default="USD")
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="invoices")


class PurchaseOrder(Base):
    """Purchase orders"""
    __tablename__ = "purchase_orders"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    vendor_id = Column(String(36), ForeignKey("vendors.id"))
    document_id = Column(String(36), ForeignKey("documents.id"))
    
    po_number = Column(String(100), nullable=False)
    po_date = Column(DateTime)
    expected_delivery_date = Column(DateTime)
    
    total_amount = Column(Numeric(15, 2))
    status = Column(String(20))  # draft, sent, confirmed, received, closed
    
    line_items = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class SalesOrder(Base):
    """Sales orders"""
    __tablename__ = "sales_orders"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    customer_id = Column(String(36), ForeignKey("customers.id"))
    document_id = Column(String(36), ForeignKey("documents.id"))
    
    so_number = Column(String(100), nullable=False)
    so_date = Column(DateTime)
    expected_delivery_date = Column(DateTime)
    
    total_amount = Column(Numeric(15, 2))
    status = Column(String(20))  # draft, confirmed, shipped, delivered, closed
    
    line_items = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class BankTransaction(Base):
    """Bank transactions from statements"""
    __tablename__ = "bank_transactions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    bank_account_id = Column(String(36), ForeignKey("bank_accounts.id"))
    document_id = Column(String(36), ForeignKey("documents.id"))
    
    transaction_date = Column(DateTime)
    transaction_id = Column(String(100))  # Bank's transaction ID
    
    description = Column(Text)
    reference = Column(String(100))
    
    debit_amount = Column(Numeric(15, 2), default=0)
    credit_amount = Column(Numeric(15, 2), default=0)
    balance = Column(Numeric(15, 2))
    
    # Categorization
    category = Column(String(100))
    is_reconciled = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    bank_account = relationship("BankAccount", back_populates="transactions")


class CreditDebitNote(Base):
    """Credit and Debit notes"""
    __tablename__ = "credit_debit_notes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    document_id = Column(String(36), ForeignKey("documents.id"))
    
    note_type = Column(String(20))  # credit_note, debit_note
    note_number = Column(String(100), nullable=False)
    note_date = Column(DateTime)
    
    # Reference to original invoice
    reference_invoice_id = Column(String(36))
    reference_invoice_number = Column(String(100))
    
    # Party info
    party_type = Column(String(20))  # vendor, customer
    party_id = Column(String(36))
    party_name = Column(String(255))
    
    # Amount
    total_amount = Column(Numeric(15, 2))
    
    reason = Column(Text)
    line_items = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class ExpenseBill(Base):
    """Expense bills/receipts"""
    __tablename__ = "expense_bills"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    document_id = Column(String(36), ForeignKey("documents.id"))
    
    bill_number = Column(String(100))
    bill_date = Column(DateTime)
    
    vendor_name = Column(String(255))
    
    category = Column(String(100))  # travel, meals, office_supplies, etc.
    total_amount = Column(Numeric(15, 2))
    
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.UNPAID)
    
    description = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# EXTRACTION RULES
# ============================================================================

class ExtractionRule(Base):
    """Rules for extracting data from different document types"""
    __tablename__ = "extraction_rules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"))
    
    document_type = Column(Enum(DocumentType), nullable=False)
    
    # Extraction configuration (JSON)
    # Defines what fields to extract and how
    extraction_config = Column(JSON)
    
    # Example:
    # {
    #   "vendor_invoice": {
    #     "required_fields": ["invoice_number", "total_amount", "vendor_name"],
    #     "optional_fields": ["po_number", "tax_amount"],
    #     "field_mapping": {
    #       "seller.name": "vendor_name",
    #       "document_metadata.document_number": "invoice_number"
    #     }
    #   }
    # }
    
    is_default = Column(Boolean, default=False)
    priority = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)