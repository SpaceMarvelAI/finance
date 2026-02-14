"""
Persistent Database Manager
Stores uploaded documents in PostgreSQL database
"""

import psycopg2
import psycopg2.extras
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class DatabaseManager:
    """
    Manages persistent storage of financial documents in PostgreSQL
    
    Tables:
    - documents: All uploaded documents with parsed data
    - metadata: System metadata
    """
    
    def __init__(self, 
                 host: str = None,
                 port: int = None,
                 database: str = None,
                 user: str = None,
                 password: str = None):
        
        # Use environment variables or defaults
        self.host = host or os.getenv("DB_HOST", "localhost")
        self.port = port or int(os.getenv("DB_PORT", "5432"))
        self.database = database or os.getenv("DB_NAME", "financial_automation")
        self.user = user or os.getenv("DB_USER", "postgres")
        self.password = password or os.getenv("DB_PASSWORD", "postgres")
        
        self.conn = None
        self.initialize_database()
        
        logger.info(f"PostgreSQL database initialized: {self.database}@{self.host}")
    
    def initialize_database(self):
        """Create database connection (tables already exist in production)"""
        # Check if a full DATABASE_URL exists first
        db_url = os.getenv("DATABASE_URL")
        
        if db_url:
            # Connect using the single connection string
            self.conn = psycopg2.connect(db_url)
        else:
            # Fall back to individual variables
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
        
        # Use RealDictCursor for dictionary results
        self.conn.autocommit = False
        
        logger.info("PostgreSQL connection established")
    
    def insert_document(self, document_data: Dict[str, Any]) -> str:
        """
        Insert a new document into the PostgreSQL database
        
        Args:
            document_data: Document data dictionary
            
        Returns:
            Document ID (string UUID)
        """
        cursor = self.conn.cursor()
        
        # Prepare data
        company_id = document_data.get("company_id", "default")
        file_name = document_data.get("file_name", "")
        file_path = document_data.get("file_path", "")
        file_type = Path(file_name).suffix.lstrip('.') if file_name else ""
        
        document_number = document_data.get("document_number", "")
        
        #  FIX: Parse invoice_date string to proper DATE object (date only, no time)
        document_date_str = document_data.get("document_date", "")
        document_date = None
        
        if document_date_str:
            document_date = self._parse_date(document_date_str)
            # Ensure it's a date object, not datetime
            if document_date and hasattr(document_date, 'date'):
                document_date = document_date.date()
        
        category = document_data.get("category", "")
        
        #  FIX: Get amounts and convert currency using LIVE RATES
        grand_total = document_data.get("grand_total", 0.0)
        tax_total = document_data.get("tax_total", 0.0)
        paid_amount = document_data.get("paid_amount", 0.0)
        detected_currency = document_data.get("detected_currency", "INR")  # FIX: Default to INR
        
        # Convert to INR if needed using live exchange rates
        original_total = grand_total
        original_tax = tax_total
        original_paid = paid_amount
        
        if detected_currency != "INR" and grand_total > 0:
            try:
                from shared.utils.live_exchange_rates import get_rate_provider
                
                rate_provider = get_rate_provider()
                original_total = grand_total

                # Convert with live rates based on invoice date
                grand_total = rate_provider.convert(original_total, detected_currency, document_date_str)
                tax_total = rate_provider.convert(tax_total, detected_currency, document_date_str) if tax_total else 0.0
                paid_amount = rate_provider.convert(original_paid, detected_currency, document_date_str) if paid_amount else 0.0
                
                # Get rate for logging
                rate = rate_provider.get_rate_for_date(detected_currency, document_date_str)
                logger.info(f"💱 Converted {detected_currency} {original_total} → INR ₹{grand_total:.2f}")
                
            except Exception as e:
                logger.warning(f"⚠️ Live currency conversion failed: {e}, using fallback")
                # Fallback to static rates
                try:
                    from shared.utils.currency_converter import CurrencyConverter
                    converter = CurrencyConverter()
                    grand_total = converter.convert_to_inr(original_total, detected_currency)
                    tax_total = converter.convert_to_inr(original_tax, detected_currency) if tax_total else 0.0
                    paid_amount = converter.convert_to_inr(original_paid, detected_currency) if paid_amount else 0.0
                    logger.info(f"💱 Converted using fallback rates: {detected_currency} → INR ₹{grand_total:.2f}")
                except Exception as fallback_error:
                    logger.warning(f"⚠️ All currency conversion failed: {fallback_error}, keeping original amounts")
                    # Keep original amounts but mark as INR since we can't convert
                    grand_total = original_total
                    tax_total = original_tax
                    paid_amount = original_paid
                    detected_currency = "INR"
        else:
            # Already in INR or no amount
            logger.info(f"✅ Amount already in INR: ₹{grand_total:.2f}")
        
        outstanding = grand_total - paid_amount
        
        # Extract vendor/customer names from document_data directly
        vendor_name = document_data.get("vendor_name", "")
        customer_name = document_data.get("customer_name", "")
        
        # Prepare JSON data
        docling_parsed_data = json.dumps(document_data.get("parsed_data", {}))
        canonical_data_json = json.dumps(document_data.get("canonical_data", {}))
        
        uploaded_at = datetime.now()
        processed_at = uploaded_at
        
        # Get or generate document ID
        doc_id = document_data.get("id") or str(uuid.uuid4())
        
        # INSERT matching actual schema
        cursor.execute("""
            INSERT INTO documents (
                id, company_id, file_name, file_path, file_type,
                document_number, document_date, category,
                grand_total, tax_total, paid_amount, outstanding,
                vendor_name, customer_name,
                docling_parsed_data, canonical_data,
                uploaded_at, processed_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            doc_id, company_id, file_name, file_path, file_type,
            document_number, document_date, category,  # document_date is already a date object
            grand_total, tax_total, paid_amount, outstanding,
            vendor_name, customer_name,
            docling_parsed_data, canonical_data_json,
            uploaded_at, processed_at
        ))
        
        self.conn.commit()
        
        logger.info(f" Document inserted: ID={doc_id}, ₹{grand_total:.2f} total, Date={document_date}")
        
        return doc_id
    
    def _parse_date(self, date_str: str) -> Optional[Any]:
        """
        Parse date string to DATE object (handles all formats)
        
        Supported formats:
        - "8/15/2025", "15/8/2025"
        - "2025-08-15"
        - "August 20, 2025", "20 August 2025"
        - "Aug 20, 2025", "20 Aug 2025"
        """
        if not date_str or date_str == "":
            return None
        
        # Try multiple date formats
        date_formats = [
            '%m/%d/%Y',          # 8/15/2025
            '%d/%m/%Y',          # 15/8/2025
            '%Y-%m-%d',          # 2025-08-15
            '%B %d, %Y',         # August 20, 2025
            '%d %B %Y',          # 20 August 2025
            '%b %d, %Y',         # Aug 20, 2025
            '%d %b %Y',          # 20 Aug 2025
            '%Y/%m/%d',          # 2025/08/15
            '%d-%m-%Y',          # 15-08-2025
            '%m-%d-%Y',          # 08-15-2025
        ]
        
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str.strip(), fmt)
                # Return just the date part (not datetime with time)
                return date_obj.date()
            except ValueError:
                continue
        
        # If all formats fail, log warning and return None
        logger.warning(f"⚠️ Could not parse date: '{date_str}'")
        return None
    
    def get_all_documents(self, company_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all documents from PostgreSQL database
        
        Args:
            company_id: Filter by company (optional)
            
        Returns:
            List of document dictionaries
        """
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        if company_id:
            cursor.execute("""
                SELECT * FROM documents 
                WHERE company_id = %s
                ORDER BY uploaded_at DESC
            """, (company_id,))
        else:
            cursor.execute("""
                SELECT * FROM documents 
                ORDER BY uploaded_at DESC
            """)
        
        rows = cursor.fetchall()
        
        documents = []
        for row in rows:
            doc = dict(row)
            
            # PostgreSQL JSONB is automatically deserialized
            # But if it's still a string, parse it
            if isinstance(doc.get('docling_parsed_data'), str):
                doc['docling_parsed_data'] = json.loads(doc['docling_parsed_data'])
            if isinstance(doc.get('canonical_data'), str):
                doc['canonical_data'] = json.loads(doc['canonical_data'])
            
            # Convert datetime/date to ISO string for JSON serialization
            for field in ['uploaded_at', 'processed_at', 'created_at', 'document_date']:
                if doc.get(field):
                    doc[field] = doc[field].isoformat() if hasattr(doc[field], 'isoformat') else str(doc[field])
            
            documents.append(doc)
        
        logger.info(f"Retrieved {len(documents)} documents from PostgreSQL")
        
        return documents
    
    def get_documents_by_category(self, category: str, company_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get documents filtered by category from PostgreSQL
        
        Args:
            category: Document category (purchase, sales, etc.)
            company_id: Filter by company (optional)
            
        Returns:
            List of document dictionaries
        """
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        if company_id:
            cursor.execute("""
                SELECT * FROM documents 
                WHERE category = %s AND company_id = %s
                ORDER BY document_date DESC NULLS LAST, uploaded_at DESC
            """, (category, company_id))
        else:
            cursor.execute("""
                SELECT * FROM documents 
                WHERE category = %s
                ORDER BY document_date DESC NULLS LAST, uploaded_at DESC
            """, (category,))
        
        rows = cursor.fetchall()
        
        documents = []
        for row in rows:
            doc = dict(row)
            
            # Handle JSONB
            if isinstance(doc.get('docling_parsed_data'), str):
                doc['docling_parsed_data'] = json.loads(doc['docling_parsed_data'])
            if isinstance(doc.get('canonical_data'), str):
                doc['canonical_data'] = json.loads(doc['canonical_data'])
            
            # Convert datetime/date
            for field in ['uploaded_at', 'processed_at', 'document_date']:
                if doc.get(field):
                    doc[field] = doc[field].isoformat() if hasattr(doc[field], 'isoformat') else str(doc[field])
            
            documents.append(doc)
        
        logger.info(f"Retrieved {len(documents)} {category} documents from PostgreSQL")
        
        return documents
    
    def get_document_by_id(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID from PostgreSQL"""
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("SELECT * FROM documents WHERE id = %s", (doc_id,))
        row = cursor.fetchone()
        
        if row:
            doc = dict(row)
            
            if isinstance(doc.get('docling_parsed_data'), str):
                doc['docling_parsed_data'] = json.loads(doc['docling_parsed_data'])
            if isinstance(doc.get('canonical_data'), str):
                doc['canonical_data'] = json.loads(doc['canonical_data'])
            
            return doc
        
        return None
    
    def delete_document(self, doc_id: int) -> bool:
        """Delete a document from PostgreSQL"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
        self.conn.commit()
        
        deleted = cursor.rowcount > 0
        logger.info(f"Document {doc_id} deleted from PostgreSQL: {deleted}")
        
        return deleted
    
    def get_company_aliases(self, company_id: str) -> List[str]:
        """
        Get company aliases for a company
        
        Args:
            company_id: Company ID
            
        Returns:
            List of company aliases
        """
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute("""
            SELECT company_aliases FROM companies WHERE id = %s
        """, (company_id,))
        
        row = cursor.fetchone()
        
        if row and row.get('company_aliases'):
            aliases = row['company_aliases']
            # Ensure it's a list
            if isinstance(aliases, list):
                return aliases
            elif isinstance(aliases, str):
                # Parse JSON string if needed
                try:
                    import json
                    return json.loads(aliases)
                except:
                    return []
        
        return []
    
    def get_statistics(self, company_id: Optional[str] = None) -> Dict[str, Any]:
        """Get database statistics from PostgreSQL"""
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        if company_id:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_documents,
                    COUNT(CASE WHEN category = 'purchase' THEN 1 END) as purchase_count,
                    COUNT(CASE WHEN category = 'sales' THEN 1 END) as sales_count,
                    SUM(CASE WHEN category = 'purchase' THEN grand_total ELSE 0 END) as total_purchases,
                    SUM(CASE WHEN category = 'sales' THEN grand_total ELSE 0 END) as total_sales,
                    SUM(CASE WHEN category = 'purchase' THEN outstanding ELSE 0 END) as total_payables,
                    SUM(CASE WHEN category = 'sales' THEN outstanding ELSE 0 END) as total_receivables
                FROM documents
                WHERE company_id = %s
            """, (company_id,))
        else:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_documents,
                    COUNT(CASE WHEN category = 'purchase' THEN 1 END) as purchase_count,
                    COUNT(CASE WHEN category = 'sales' THEN 1 END) as sales_count,
                    SUM(CASE WHEN category = 'purchase' THEN grand_total ELSE 0 END) as total_purchases,
                    SUM(CASE WHEN category = 'sales' THEN grand_total ELSE 0 END) as total_sales,
                    SUM(CASE WHEN category = 'purchase' THEN outstanding ELSE 0 END) as total_payables,
                    SUM(CASE WHEN category = 'sales' THEN outstanding ELSE 0 END) as total_receivables
                FROM documents
            """)
        
        row = cursor.fetchone()
        
        return {
            "total_documents": int(row['total_documents']) if row['total_documents'] else 0,
            "purchase_invoices": int(row['purchase_count']) if row['purchase_count'] else 0,
            "sales_invoices": int(row['sales_count']) if row['sales_count'] else 0,
            "total_purchases": float(row['total_purchases']) if row['total_purchases'] else 0.0,
            "total_sales": float(row['total_sales']) if row['total_sales'] else 0.0,
            "total_payables": float(row['total_payables']) if row['total_payables'] else 0.0,
            "total_receivables": float(row['total_receivables']) if row['total_receivables'] else 0.0
        }
    
    def close(self):
        """Close PostgreSQL database connection"""
        if self.conn:
            self.conn.close()
            logger.info("PostgreSQL connection closed")


# Global database instance
_db_instance = None

def get_database() -> DatabaseManager:
    """Get or create database instance (singleton)"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance