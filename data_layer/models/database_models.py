"""
Complete Database Models for Financial Automation System
Includes: Companies, Vendors, Customers, Invoices, Payments, Bank Accounts, Reconciliation
"""

from sqlalchemy import Column, String, Integer, Numeric, Date, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid


Base = declarative_base()


class Company(Base):
    """Company/Tenant Master"""
    __tablename__ = "companies"
    
    company_id = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255))
    tax_id = Column(String(50))
    
    # Address
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    # Contact
    phone = Column(String(50))
    email = Column(String(255))
    website = Column(String(255))
    
    # Branding
    logo_path = Column(String(500))
    
    # Financial Settings
    currency = Column(String(3), default='USD')
    fiscal_year_start = Column(String(5), default='01-01')  # MM-DD format
    
    # Additional Settings (JSON)
    settings = Column(JSONB)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vendors = relationship("Vendor", back_populates="company")
    customers = relationship("Customer", back_populates="company")
    vendor_invoices = relationship("Invoice", back_populates="company", foreign_keys="Invoice.company_id")
    payments = relationship("Payment", back_populates="company")


class Vendor(Base):
    """Vendor/Supplier Master"""
    __tablename__ = "vendors"
    
    vendor_id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.company_id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255))
    tax_id = Column(String(50))
    
    # Address
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    # Contact
    phone = Column(String(50))
    email = Column(String(255))
    website = Column(String(255))
    
    # Payment Terms
    payment_terms = Column(Integer, default=30)  # Days
    
    # Financial
    currency = Column(String(3), default='USD')
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="vendors")
    invoices = relationship("Invoice", back_populates="vendor")


class Customer(Base):
    """Customer Master"""
    __tablename__ = "customers"
    
    customer_id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.company_id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255))
    tax_id = Column(String(50))
    
    # Address
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    # Contact
    phone = Column(String(50))
    email = Column(String(255))
    website = Column(String(255))
    
    # Payment Terms
    payment_terms = Column(Integer, default=30)  # Days
    credit_limit = Column(Numeric(15, 2))
    
    # Financial
    currency = Column(String(3), default='USD')
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="customers")
    invoices = relationship("CustomerInvoice", back_populates="customer")


class Invoice(Base):
    """Vendor Invoice (Accounts Payable)"""
    __tablename__ = "vendor_invoices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(String(50), ForeignKey("companies.company_id"), nullable=False)
    vendor_id = Column(String(50), ForeignKey("vendors.vendor_id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"))
    
    invoice_number = Column(String(100), unique=True, nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date)
    
    # Amounts
    subtotal = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), nullable=False)
    paid_amount = Column(Numeric(15, 2), default=0)
    outstanding_amount = Column(Numeric(15, 2))
    
    # Status
    payment_status = Column(String(20), default='unpaid')  # unpaid, partial, paid, overdue
    
    # Line Items (JSON)
    line_items = Column(JSONB)
    
    # Currency
    currency = Column(String(3), default='USD')
    
    # Notes
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="vendor_invoices")
    vendor = relationship("Vendor", back_populates="invoices")
    payments = relationship("Payment", back_populates="vendor_invoice")


class CustomerInvoice(Base):
    """Customer Invoice (Accounts Receivable)"""
    __tablename__ = "customer_invoices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(String(50), ForeignKey("companies.company_id"), nullable=False)
    customer_id = Column(String(50), ForeignKey("customers.customer_id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"))
    
    invoice_number = Column(String(100), unique=True, nullable=False)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date)
    
    # Amounts
    subtotal = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), nullable=False)
    paid_amount = Column(Numeric(15, 2), default=0)
    outstanding_amount = Column(Numeric(15, 2))
    
    # Status
    payment_status = Column(String(20), default='unpaid')  # unpaid, partial, paid, overdue
    
    # Line Items (JSON)
    line_items = Column(JSONB)
    
    # Currency
    currency = Column(String(3), default='USD')
    
    # Notes
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer = relationship("Customer", back_populates="invoices")
    payments = relationship("Payment", back_populates="customer_invoice")


class Payment(Base):
    """Payment Records"""
    __tablename__ = "payments"
    
    payment_id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.company_id"), nullable=False)
    
    # Links to invoices
    vendor_invoice_id = Column(Integer, ForeignKey("vendor_invoices.id"))
    customer_invoice_id = Column(Integer, ForeignKey("customer_invoices.id"))
    
    payment_date = Column(Date, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    
    # Payment Method
    payment_method = Column(String(50))  # cash, check, wire, card, etc.
    reference_number = Column(String(100))
    
    # Currency
    currency = Column(String(3), default='USD')
    
    # Notes
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = relationship("Company", back_populates="payments")
    vendor_invoice = relationship("Invoice", back_populates="payments")
    customer_invoice = relationship("CustomerInvoice", back_populates="payments")


class BankAccount(Base):
    """Bank Account Master"""
    __tablename__ = "bank_accounts"
    
    account_id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.company_id"), nullable=False)
    
    account_name = Column(String(255), nullable=False)
    account_number = Column(String(100))
    bank_name = Column(String(255))
    
    # Currency
    currency = Column(String(3), default='USD')
    
    # Balance
    current_balance = Column(Numeric(15, 2), default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = relationship("BankTransaction", back_populates="account")


class BankTransaction(Base):
    """Bank Transactions (from bank statements)"""
    __tablename__ = "bank_transactions"
    
    transaction_id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.company_id"), nullable=False)
    account_id = Column(String(50), ForeignKey("bank_accounts.account_id"), nullable=False)
    
    transaction_date = Column(Date, nullable=False)
    description = Column(Text)
    reference = Column(String(100))
    
    # Amounts
    debit = Column(Numeric(15, 2))
    credit = Column(Numeric(15, 2))
    balance = Column(Numeric(15, 2))
    
    # Currency
    currency = Column(String(3), default='USD')
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    account = relationship("BankAccount", back_populates="transactions")
    reconciliation = relationship("ReconciliationRecord", back_populates="bank_transaction")


class ReconciliationRecord(Base):
    """Reconciliation Matching Records"""
    __tablename__ = "reconciliation_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(String(50), ForeignKey("companies.company_id"), nullable=False)
    
    # Links to transactions
    bank_transaction_id = Column(String(50), ForeignKey("bank_transactions.transaction_id"))
    invoice_id = Column(Integer)  # Can be vendor or customer invoice
    payment_id = Column(String(50), ForeignKey("payments.payment_id"))
    
    # Match Details
    match_type = Column(String(20))  # exact, partial, unmatched
    difference_amount = Column(Numeric(15, 2))
    
    # Reconciliation Metadata
    reconciled_at = Column(DateTime)
    reconciled_by = Column(String(100))
    notes = Column(Text)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    bank_transaction = relationship("BankTransaction", back_populates="reconciliation")


class Document(Base):
    """Document Storage (File Uploads)"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(String(50), ForeignKey("companies.company_id"), nullable=False)
    
    # File Info
    document_type = Column(String(50))  # invoice, receipt, bank_statement, etc.
    file_name = Column(String(500))
    file_path = Column(String(1000))
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    # Parsed Data (JSON)
    parsed_data = Column(JSONB)
    canonical_data = Column(JSONB)
    
    # Processing Status
    status = Column(String(50), default='uploaded')  # uploaded, processing, completed, failed
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    """User Management"""
    __tablename__ = "users"
    
    user_id = Column(String(50), primary_key=True)
    company_id = Column(String(50), ForeignKey("companies.company_id"), nullable=False)
    
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255))
    
    # Profile
    full_name = Column(String(255))
    role = Column(String(50), default='user')  # admin, user, viewer
    
    # Status
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Convenience alias for backward compatibility
VendorInvoice = Invoice