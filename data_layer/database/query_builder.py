"""
Database Query Builder for AP/AR Data Fetching
Provides optimized queries for Accounts Payable and Accounts Receivable reports
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
import psycopg2.extras
from data_layer.database.database_manager import get_database


class APQueryBuilder:
    """
    Query builder for Accounts Payable (Vendor Invoices) data
    """
    
    def __init__(self, company_id: str):
        self.company_id = company_id
        self.db = get_database()
    
    def build_aging_query(self, as_of_date: Optional[date] = None) -> str:
        """Build query for AP aging report"""
        if not as_of_date:
            as_of_date = date.today()
        
        return f"""
            SELECT 
                vi.id,
                vi.invoice_number,
                vi.invoice_date,
                vi.due_date,
                vi.total_amount,
                vi.paid_amount,
                vi.outstanding_amount,
                vi.original_currency,
                vi.exchange_rate,
                vi.inr_amount,
                vi.payment_status,
                vi.payment_terms_days,
                v.vendor_name,
                v.vendor_code,
                v.tax_id as vendor_tax_id,
                v.email as vendor_email,
                v.phone as vendor_phone,
                v.address_line1 as vendor_address1,
                v.address_line2 as vendor_address2,
                v.city as vendor_city,
                v.state as vendor_state,
                v.country as vendor_country,
                v.postal_code as vendor_postal_code,
                d.file_name,
                d.document_number,
                d.document_date,
                vi.created_at,
                -- Calculate aging buckets
                CASE 
                    WHEN vi.due_date IS NULL THEN 'Not Due'
                    WHEN vi.due_date > '{as_of_date}' THEN 'Not Due'
                    WHEN vi.due_date <= '{as_of_date}' AND vi.due_date > '{as_of_date - datetime.timedelta(days=30)}' THEN '1-30 Days'
                    WHEN vi.due_date <= '{as_of_date - datetime.timedelta(days=30)}' AND vi.due_date > '{as_of_date - datetime.timedelta(days=60)}' THEN '31-60 Days'
                    WHEN vi.due_date <= '{as_of_date - datetime.timedelta(days=60)}' AND vi.due_date > '{as_of_date - datetime.timedelta(days=90)}' THEN '61-90 Days'
                    ELSE '90+ Days'
                END as aging_bucket,
                -- Days overdue
                CASE 
                    WHEN vi.due_date IS NULL THEN 0
                    WHEN vi.due_date > '{as_of_date}' THEN 0
                    ELSE EXTRACT(DAY FROM '{as_of_date}'::date - vi.due_date::date)::integer
                END as days_overdue
            FROM vendor_invoices vi
            LEFT JOIN vendors v ON vi.vendor_id = v.id
            LEFT JOIN documents d ON vi.document_id = d.id
            WHERE vi.company_id = %s
                AND vi.outstanding_amount > 0
                AND vi.invoice_date <= '{as_of_date}'
            ORDER BY vi.due_date ASC, vi.invoice_date DESC
        """
    
    def build_register_query(self, date_from: Optional[date] = None, date_to: Optional[date] = None) -> str:
        """Build query for AP register report"""
        where_clauses = ["vi.company_id = %s"]
        params = [self.company_id]
        
        if date_from:
            where_clauses.append("vi.invoice_date >= %s")
            params.append(date_from)
        
        if date_to:
            where_clauses.append("vi.invoice_date <= %s")
            params.append(date_to)
        
        where_clause = " AND ".join(where_clauses)
        
        return f"""
            SELECT 
                vi.id,
                vi.invoice_number,
                vi.invoice_date,
                vi.due_date,
                vi.subtotal_amount,
                vi.tax_amount,
                vi.total_amount,
                vi.paid_amount,
                vi.outstanding_amount,
                vi.original_currency,
                vi.exchange_rate,
                vi.inr_amount,
                vi.payment_status,
                vi.payment_terms_days,
                v.vendor_name,
                v.vendor_code,
                v.tax_id as vendor_tax_id,
                v.email as vendor_email,
                v.phone as vendor_phone,
                d.file_name,
                d.document_number,
                vi.created_at
            FROM vendor_invoices vi
            LEFT JOIN vendors v ON vi.vendor_id = v.id
            LEFT JOIN documents d ON vi.document_id = d.id
            WHERE {where_clause}
            ORDER BY vi.invoice_date DESC, vi.created_at DESC
        """, params
    
    def build_overdue_query(self, as_of_date: Optional[date] = None) -> str:
        """Build query for overdue invoices"""
        if not as_of_date:
            as_of_date = date.today()
        
        return f"""
            SELECT 
                vi.id,
                vi.invoice_number,
                vi.invoice_date,
                vi.due_date,
                vi.total_amount,
                vi.paid_amount,
                vi.outstanding_amount,
                vi.original_currency,
                vi.exchange_rate,
                vi.inr_amount,
                vi.payment_status,
                v.vendor_name,
                v.vendor_code,
                v.email as vendor_email,
                v.phone as vendor_phone,
                d.file_name,
                -- Calculate days overdue
                EXTRACT(DAY FROM '{as_of_date}'::date - vi.due_date::date)::integer as days_overdue
            FROM vendor_invoices vi
            LEFT JOIN vendors v ON vi.vendor_id = v.id
            LEFT JOIN documents d ON vi.document_id = d.id
            WHERE vi.company_id = %s
                AND vi.outstanding_amount > 0
                AND vi.due_date < '{as_of_date}'
                AND vi.due_date IS NOT NULL
            ORDER BY days_overdue DESC, vi.outstanding_amount DESC
        """
    
    def build_vendor_summary_query(self) -> str:
        """Build query for vendor summary"""
        return f"""
            SELECT 
                v.id as vendor_id,
                v.vendor_name,
                v.vendor_code,
                v.tax_id as vendor_tax_id,
                v.email as vendor_email,
                v.phone as vendor_phone,
                COUNT(vi.id) as total_invoices,
                SUM(vi.total_amount) as total_amount,
                SUM(vi.paid_amount) as total_paid,
                SUM(vi.outstanding_amount) as total_outstanding,
                AVG(vi.payment_terms_days) as avg_payment_terms,
                MIN(vi.invoice_date) as first_invoice_date,
                MAX(vi.invoice_date) as last_invoice_date,
                -- Count overdue
                COUNT(CASE WHEN vi.outstanding_amount > 0 AND vi.due_date < CURRENT_DATE THEN 1 END) as overdue_count,
                SUM(CASE WHEN vi.outstanding_amount > 0 AND vi.due_date < CURRENT_DATE THEN vi.outstanding_amount ELSE 0 END) as overdue_amount
            FROM vendors v
            LEFT JOIN vendor_invoices vi ON v.id = vi.vendor_id
            WHERE v.company_id = %s
            GROUP BY v.id, v.vendor_name, v.vendor_code, v.tax_id, v.email, v.phone
            HAVING COUNT(vi.id) > 0
            ORDER BY total_outstanding DESC, vendor_name
        """


class ARQueryBuilder:
    """
    Query builder for Accounts Receivable (Customer Invoices) data
    """
    
    def __init__(self, company_id: str):
        self.company_id = company_id
        self.db = get_database()
    
    def build_aging_query(self, as_of_date: Optional[date] = None) -> str:
        """Build query for AR aging report"""
        if not as_of_date:
            as_of_date = date.today()
        
        return f"""
            SELECT 
                ci.id,
                ci.invoice_number,
                ci.invoice_date,
                ci.due_date,
                ci.total_amount,
                ci.received_amount,
                ci.outstanding_amount,
                ci.original_currency,
                ci.exchange_rate,
                ci.inr_amount,
                ci.payment_status,
                ci.payment_terms_days,
                c.customer_name,
                c.customer_code,
                c.tax_id as customer_tax_id,
                c.email as customer_email,
                c.phone as customer_phone,
                c.address_line1 as customer_address1,
                c.address_line2 as customer_address2,
                c.city as customer_city,
                c.state as customer_state,
                c.country as customer_country,
                c.postal_code as customer_postal_code,
                d.file_name,
                d.document_number,
                d.document_date,
                ci.created_at,
                -- Calculate aging buckets
                CASE 
                    WHEN ci.due_date IS NULL THEN 'Not Due'
                    WHEN ci.due_date > '{as_of_date}' THEN 'Not Due'
                    WHEN ci.due_date <= '{as_of_date}' AND ci.due_date > '{as_of_date - datetime.timedelta(days=30)}' THEN '1-30 Days'
                    WHEN ci.due_date <= '{as_of_date - datetime.timedelta(days=30)}' AND ci.due_date > '{as_of_date - datetime.timedelta(days=60)}' THEN '31-60 Days'
                    WHEN ci.due_date <= '{as_of_date - datetime.timedelta(days=60)}' AND ci.due_date > '{as_of_date - datetime.timedelta(days=90)}' THEN '61-90 Days'
                    ELSE '90+ Days'
                END as aging_bucket,
                -- Days overdue
                CASE 
                    WHEN ci.due_date IS NULL THEN 0
                    WHEN ci.due_date > '{as_of_date}' THEN 0
                    ELSE EXTRACT(DAY FROM '{as_of_date}'::date - ci.due_date::date)::integer
                END as days_overdue
            FROM customer_invoices ci
            LEFT JOIN customers c ON ci.customer_id = c.id
            LEFT JOIN documents d ON ci.document_id = d.id
            WHERE ci.company_id = %s
                AND ci.outstanding_amount > 0
                AND ci.invoice_date <= '{as_of_date}'
            ORDER BY ci.due_date ASC, ci.invoice_date DESC
        """
    
    def build_register_query(self, date_from: Optional[date] = None, date_to: Optional[date] = None) -> str:
        """Build query for AR register report"""
        where_clauses = ["ci.company_id = %s"]
        params = [self.company_id]
        
        if date_from:
            where_clauses.append("ci.invoice_date >= %s")
            params.append(date_from)
        
        if date_to:
            where_clauses.append("ci.invoice_date <= %s")
            params.append(date_to)
        
        where_clause = " AND ".join(where_clauses)
        
        return f"""
            SELECT 
                ci.id,
                ci.invoice_number,
                ci.invoice_date,
                ci.due_date,
                ci.subtotal_amount,
                ci.tax_amount,
                ci.total_amount,
                ci.received_amount,
                ci.outstanding_amount,
                ci.original_currency,
                ci.exchange_rate,
                ci.inr_amount,
                ci.payment_status,
                ci.payment_terms_days,
                c.customer_name,
                c.customer_code,
                c.tax_id as customer_tax_id,
                c.email as customer_email,
                c.phone as customer_phone,
                d.file_name,
                d.document_number,
                ci.created_at
            FROM customer_invoices ci
            LEFT JOIN customers c ON ci.customer_id = c.id
            LEFT JOIN documents d ON ci.document_id = d.id
            WHERE {where_clause}
            ORDER BY ci.invoice_date DESC, ci.created_at DESC
        """, params
    
    def build_collection_query(self, as_of_date: Optional[date] = None) -> str:
        """Build query for collection report"""
        if not as_of_date:
            as_of_date = date.today()
        
        return f"""
            SELECT 
                ci.id,
                ci.invoice_number,
                ci.invoice_date,
                ci.due_date,
                ci.total_amount,
                ci.received_amount,
                ci.outstanding_amount,
                ci.original_currency,
                ci.exchange_rate,
                ci.inr_amount,
                ci.payment_status,
                c.customer_name,
                c.customer_code,
                c.email as customer_email,
                c.phone as customer_phone,
                c.address_line1 as customer_address1,
                c.address_line2 as customer_address2,
                c.city as customer_city,
                c.state as customer_state,
                c.country as customer_country,
                c.postal_code as customer_postal_code,
                d.file_name,
                -- Calculate days overdue
                EXTRACT(DAY FROM '{as_of_date}'::date - ci.due_date::date)::integer as days_overdue,
                -- Calculate DSO for this invoice
                CASE 
                    WHEN ci.invoice_date IS NOT NULL THEN 
                        EXTRACT(DAY FROM '{as_of_date}'::date - ci.invoice_date::date)::integer
                    ELSE 0
                END as days_since_invoice
            FROM customer_invoices ci
            LEFT JOIN customers c ON ci.customer_id = c.id
            LEFT JOIN documents d ON ci.document_id = d.id
            WHERE ci.company_id = %s
                AND ci.outstanding_amount > 0
                AND ci.due_date < '{as_of_date}'
                AND ci.due_date IS NOT NULL
            ORDER BY days_overdue DESC, ci.outstanding_amount DESC
        """
    
    def build_dso_query(self, as_of_date: Optional[date] = None) -> str:
        """Build query for DSO calculation"""
        if not as_of_date:
            as_of_date = date.today()
        
        return f"""
            WITH ar_data AS (
                SELECT 
                    ci.customer_id,
                    c.customer_name,
                    SUM(ci.outstanding_amount) as total_outstanding,
                    SUM(CASE 
                        WHEN ci.invoice_date >= '{as_of_date - datetime.timedelta(days=90)}' 
                        THEN ci.total_amount 
                        ELSE 0 
                    END) as sales_last_90_days
                FROM customer_invoices ci
                LEFT JOIN customers c ON ci.customer_id = c.id
                WHERE ci.company_id = %s
                    AND ci.invoice_date <= '{as_of_date}'
                GROUP BY ci.customer_id, c.customer_name
                HAVING SUM(ci.outstanding_amount) > 0
            )
            SELECT 
                customer_id,
                customer_name,
                total_outstanding,
                sales_last_90_days,
                CASE 
                    WHEN sales_last_90_days > 0 THEN 
                        (total_outstanding * 90.0) / sales_last_90_days
                    ELSE 0
                END as dso
            FROM ar_data
            WHERE sales_last_90_days > 0
            ORDER BY dso DESC, total_outstanding DESC
        """
    
    def build_customer_summary_query(self) -> str:
        """Build query for customer summary"""
        return f"""
            SELECT 
                c.id as customer_id,
                c.customer_name,
                c.customer_code,
                c.tax_id as customer_tax_id,
                c.email as customer_email,
                c.phone as customer_phone,
                COUNT(ci.id) as total_invoices,
                SUM(ci.total_amount) as total_amount,
                SUM(ci.received_amount) as total_received,
                SUM(ci.outstanding_amount) as total_outstanding,
                AVG(ci.payment_terms_days) as avg_payment_terms,
                MIN(ci.invoice_date) as first_invoice_date,
                MAX(ci.invoice_date) as last_invoice_date,
                -- Count overdue
                COUNT(CASE WHEN ci.outstanding_amount > 0 AND ci.due_date < CURRENT_DATE THEN 1 END) as overdue_count,
                SUM(CASE WHEN ci.outstanding_amount > 0 AND ci.due_date < CURRENT_DATE THEN ci.outstanding_amount ELSE 0 END) as overdue_amount
            FROM customers c
            LEFT JOIN customer_invoices ci ON c.id = ci.customer_id
            WHERE c.company_id = %s
            GROUP BY c.id, c.customer_name, c.customer_code, c.tax_id, c.email, c.phone
            HAVING COUNT(ci.id) > 0
            ORDER BY total_outstanding DESC, customer_name
        """


class DataFetcher:
    """
    Unified data fetching interface for AP/AR reports
    """
    
    def __init__(self, company_id: str):
        self.company_id = company_id
        self.db = get_database()
    
    def fetch_ap_aging(self, as_of_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Fetch AP aging data"""
        query_builder = APQueryBuilder(self.company_id)
        query = query_builder.build_aging_query(as_of_date)
        
        cursor = self.db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query, (self.company_id,))
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def fetch_ap_register(self, date_from: Optional[date] = None, date_to: Optional[date] = None) -> List[Dict[str, Any]]:
        """Fetch AP register data"""
        query_builder = APQueryBuilder(self.company_id)
        query, params = query_builder.build_register_query(date_from, date_to)
        
        cursor = self.db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def fetch_ap_overdue(self, as_of_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Fetch overdue AP invoices"""
        query_builder = APQueryBuilder(self.company_id)
        query = query_builder.build_overdue_query(as_of_date)
        
        cursor = self.db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query, (self.company_id,))
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def fetch_ap_vendor_summary(self) -> List[Dict[str, Any]]:
        """Fetch vendor summary data"""
        query_builder = APQueryBuilder(self.company_id)
        query = query_builder.build_vendor_summary_query()
        
        cursor = self.db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query, (self.company_id,))
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def fetch_ar_aging(self, as_of_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Fetch AR aging data"""
        query_builder = ARQueryBuilder(self.company_id)
        query = query_builder.build_aging_query(as_of_date)
        
        cursor = self.db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query, (self.company_id,))
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def fetch_ar_register(self, date_from: Optional[date] = None, date_to: Optional[date] = None) -> List[Dict[str, Any]]:
        """Fetch AR register data"""
        query_builder = ARQueryBuilder(self.company_id)
        query, params = query_builder.build_register_query(date_from, date_to)
        
        cursor = self.db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def fetch_ar_collection(self, as_of_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Fetch collection data"""
        query_builder = ARQueryBuilder(self.company_id)
        query = query_builder.build_collection_query(as_of_date)
        
        cursor = self.db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query, (self.company_id,))
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def fetch_ar_dso(self, as_of_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """Fetch DSO data"""
        query_builder = ARQueryBuilder(self.company_id)
        query = query_builder.build_dso_query(as_of_date)
        
        cursor = self.db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query, (self.company_id,))
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def fetch_ar_customer_summary(self) -> List[Dict[str, Any]]:
        """Fetch customer summary data"""
        query_builder = ARQueryBuilder(self.company_id)
        query = query_builder.build_customer_summary_query()
        
        cursor = self.db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query, (self.company_id,))
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def get_company_info(self) -> Dict[str, Any]:
        """Get company information for branding"""
        cursor = self.db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("""
            SELECT 
                id,
                name,
                tax_id,
                email,
                phone,
                website,
                address_line1,
                address_line2,
                city,
                state,
                country,
                postal_code,
                logo_url,
                primary_color,
                secondary_color,
                currency
            FROM companies 
            WHERE id = %s
        """, (self.company_id,))
        
        row = cursor.fetchone()
        return dict(row) if row else {}


# Factory function for easy instantiation
def get_data_fetcher(company_id: str) -> DataFetcher:
    """Get data fetcher instance for company"""
    return DataFetcher(company_id)