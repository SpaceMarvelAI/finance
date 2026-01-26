"""
DATA NODES - Pure Fetch Functions
No decisions, just retrieve data from database
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import psycopg2.extras
from processing_layer.workflows.nodes.base_node import BaseNode, register_node


@register_node
class InvoiceFetchNode(BaseNode):
    """
    Invoice Fetch Node
    Pure function to fetch invoices from database
    """

    name = "Invoice Fetch"
    category = "data"
    description = "Fetches invoices from database with filters"

    input_schema = {
        "filters": {
            "category": {"type": "string", "enum": ["purchase", "sales"]},
            "date_from": {"type": "date"},
            "date_to": {"type": "date"},
            "date_field": {
                "type": "string",
                "enum": ["created_at", "invoice_date"],
                "description": "Which date field to filter on (default: created_at)"
            },
            "status": {"type": "array"},
            "entity_ids": {"type": "array"},
            "amount_min": {"type": "number"},
            "amount_max": {"type": "number"}
        }
    }

    output_schema = {
        "invoices": {"type": "array", "description": "List of invoice records"}
    }

    def __init__(self):
        super().__init__()
        from data_layer.database.database_manager import get_database
        self.db = get_database()

    def run(self, input_data: Any = None, params: Dict[str, Any] = None) -> List[Dict]:
        params = params or {}

        category = params.get("category")
        company_id = params.get("company_id")
        date_from = params.get("date_from")
        date_to = params.get("date_to")
        date_field = params.get("date_field", "created_at")  # 🔒 backward compatible
        status = params.get("status", [])
        entity_ids = params.get("entity_ids", [])
        amount_min = params.get("amount_min")
        amount_max = params.get("amount_max")

        # Resolve company_id safely
        if not company_id:
            from shared.tools.user_settings import get_settings_manager
            settings_mgr = get_settings_manager()
            user_settings = settings_mgr.get_user_settings("default")
            company_id = user_settings.get("company_id") if user_settings else None

        cursor = self.db.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        invoices = []

        try:
            if category == "purchase":
                query = """
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
                        vi.vendor_id,
                        v.vendor_name,
                        d.file_name,
                        vi.created_at
                    FROM vendor_invoices vi
                    LEFT JOIN vendors v ON vi.vendor_id = v.id
                    LEFT JOIN documents d ON vi.document_id = d.id
                    WHERE vi.company_id = %s
                    ORDER BY vi.invoice_date DESC NULLS LAST
                """
                cursor.execute(query, (company_id,))
                rows = cursor.fetchall()

                for row in rows:
                    invoices.append({
                        "id": row["id"],
                        "invoice_number": row["invoice_number"],
                        "invoice_date": row["invoice_date"].isoformat() if row["invoice_date"] else None,
                        "due_date": row["due_date"].isoformat() if row["due_date"] else None,
                        "vendor_id": row["vendor_id"],
                        "vendor_name": row["vendor_name"] or "Unknown",
                        "subtotal_amount": float(row["subtotal_amount"] or 0),
                        "tax_amount": float(row["tax_amount"] or 0),
                        "total_amount": float(row["total_amount"] or 0),
                        "paid_amount": float(row["paid_amount"] or 0),
                        "outstanding_amount": float(row["outstanding_amount"] or 0),
                        "original_currency": row["original_currency"],
                        "exchange_rate": float(row["exchange_rate"] or 1.0),
                        "inr_amount": float(row["inr_amount"] or 0),
                        "payment_status": row["payment_status"],
                        "payment_terms_days": row["payment_terms_days"],
                        "file_name": row["file_name"],
                        "category": "purchase",
                        "created_at": row["created_at"].isoformat() if row["created_at"] else None
                    })

            elif category == "sales":
                query = """
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
                        ci.customer_id,
                        c.customer_name,
                        d.file_name,
                        ci.created_at
                    FROM customer_invoices ci
                    LEFT JOIN customers c ON ci.customer_id = c.id
                    LEFT JOIN documents d ON ci.document_id = d.id
                    WHERE ci.company_id = %s
                    ORDER BY ci.invoice_date DESC NULLS LAST
                """
                cursor.execute(query, (company_id,))
                rows = cursor.fetchall()

                for row in rows:
                    invoices.append({
                        "id": row["id"],
                        "invoice_number": row["invoice_number"],
                        "invoice_date": row["invoice_date"].isoformat() if row["invoice_date"] else None,
                        "due_date": row["due_date"].isoformat() if row["due_date"] else None,
                        "customer_id": row["customer_id"],
                        "customer_name": row["customer_name"] or "Unknown",
                        "subtotal_amount": float(row["subtotal_amount"] or 0),
                        "tax_amount": float(row["tax_amount"] or 0),
                        "total_amount": float(row["total_amount"] or 0),
                        "received_amount": float(row["received_amount"] or 0),
                        "outstanding_amount": float(row["outstanding_amount"] or 0),
                        "original_currency": row["original_currency"],
                        "exchange_rate": float(row["exchange_rate"] or 1.0),
                        "inr_amount": float(row["inr_amount"] or 0),
                        "payment_status": row["payment_status"],
                        "payment_terms_days": row["payment_terms_days"],
                        "file_name": row["file_name"],
                        "category": "sales",
                        "created_at": row["created_at"].isoformat() if row["created_at"] else None
                    })

        except Exception as e:
            self.logger.error(f"Error fetching invoices: {e}")
            import traceback
            traceback.print_exc()
        finally:
            cursor.close()

        # -------------------------------
        # SAFE, EXPLICIT FILTERING LAYER
        # -------------------------------

        parsed_date_from = (
            datetime.strptime(date_from, "%Y-%m-%d").date()
            if date_from else None
        )
        parsed_date_to = (
            datetime.strptime(date_to, "%Y-%m-%d").date()
            if date_to else None
        )

        filtered = []
        for inv in invoices:
            # Date filtering (explicit field)
            raw_date = inv.get(date_field)
            if raw_date:
                inv_date = datetime.fromisoformat(raw_date).date()

                if parsed_date_from and inv_date < parsed_date_from:
                    continue
                if parsed_date_to and inv_date > parsed_date_to:
                    continue

            # Status filter (FIXED)
            if status and inv.get("payment_status") not in status:
                continue

            # Entity filter
            if entity_ids:
                if inv.get("vendor_id") not in entity_ids and inv.get("customer_id") not in entity_ids:
                    continue

            # Amount filter
            amount = float(inv.get("inr_amount", 0))
            if amount_min and amount < amount_min:
                continue
            if amount_max and amount > amount_max:
                continue

            filtered.append(inv)

        self.logger.info(f"Fetched {len(filtered)} invoices")
        return filtered


@register_node
class PaymentFetchNode(BaseNode):
    """
    Payment Fetch Node
    Pure function to fetch payments from database
    """
    
    name = "Payment Fetch"
    category = "data"
    description = "Fetches payment records from database"
    
    input_schema = {
        "filters": {
            "invoice_ids": {"type": "array"},
            "date_from": {"type": "date"},
            "date_to": {"type": "date"},
            "payment_method": {"type": "string"}
        }
    }
    
    output_schema = {
        "payments": {"type": "array", "description": "List of payment records"}
    }
    
    def __init__(self):
        super().__init__()
        from data_layer.database.database_manager import get_database
        self.db = get_database()
    
    def run(self, input_data: Any = None, params: Dict[str, Any] = None) -> List[Dict]:
        """
        Fetch payments
        
        Args:
            input_data: Optional list of invoices (to get invoice_ids)
            params: Filter parameters
            
        Returns:
            List of payments
        """
        params = params or {}
        
        # If input_data has invoices, extract invoice_ids
        invoice_ids = params.get('invoice_ids', [])
        if input_data and isinstance(input_data, list):
            invoice_ids.extend([inv.get('id') for inv in input_data if inv.get('id')])
        
        # TODO: Implement actual payment fetch from database
        # For now, return payments from invoice paid_amount
        payments = []
        
        # TODO: Implement actual payment fetch from payment_transactions table
        # For now, payment data is already in the invoice records (paid_amount/received_amount)
        # So we just return empty list since invoices already have this data
        
        self.logger.info(f"Payment data available in invoice records")
        return payments


@register_node
class MasterDataNode(BaseNode):
    """
    Master Data Node
    Pure function to fetch vendor/customer master data
    """
    
    name = "Master Data"
    category = "data"
    description = "Fetches vendor/customer master data"
    
    input_schema = {
        "entity_type": {"type": "string", "enum": ["vendor", "customer"]},
        "entity_ids": {"type": "array"}
    }
    
    output_schema = {
        "entities": {"type": "array", "description": "List of entity records"}
    }
    
    def __init__(self):
        super().__init__()
        from data_layer.database.database_manager import get_database
        self.db = get_database()
    
    def run(self, input_data: Any = None, params: Dict[str, Any] = None) -> List[Dict]:
        """
        Fetch master data
        
        Args:
            input_data: Optional list of invoices (to extract entity_ids)
            params: Filter parameters
            
        Returns:
            List of entity records
        """
        params = params or {}
        
        entity_type = params.get('entity_type', 'vendor')
        entity_ids = params.get('entity_ids', [])
        
        # Extract entity_ids from input invoices if provided
        if input_data and isinstance(input_data, list):
            if entity_type == 'vendor':
                entity_ids.extend([inv.get('vendor_id') for inv in input_data if inv.get('vendor_id')])
            else:
                entity_ids.extend([inv.get('customer_id') for inv in input_data if inv.get('customer_id')])
        
        # Remove duplicates
        entity_ids = list(set(entity_ids))
        
        # TODO: Fetch from master data tables
        # For now, extract from invoices
        entities = {}
        invoices = self.db.get_all_documents()
        
        for inv in invoices:
            if entity_type == 'vendor':
                entity_id = inv.get('vendor_id')
                entity_name = inv.get('vendor_name')
            else:
                entity_id = inv.get('customer_id')
                entity_name = inv.get('customer_name')
            
            if entity_id and entity_id not in entities:
                entities[entity_id] = {
                    'id': entity_id,
                    'name': entity_name,
                    'type': entity_type
                }
        
        result = list(entities.values())
        self.logger.info(f"Fetched {len(result)} {entity_type} records")
        return result


@register_node
class ConfigNode(BaseNode):
    """
    Config Node
    Pure function to fetch system configuration
    """
    
    name = "Config"
    category = "data"
    description = "Fetches system configuration settings"
    
    input_schema = {
        "config_keys": {"type": "array", "description": "List of config keys to fetch"}
    }
    
    output_schema = {
        "config": {"type": "object", "description": "Configuration values"}
    }
    
    def __init__(self):
        super().__init__()
        from shared.tools.user_settings import get_settings_manager
        self.settings_mgr = get_settings_manager()
    
    def run(self, input_data: Any = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Fetch configuration
        
        Args:
            input_data: Not used
            params: Config keys to fetch
            
        Returns:
            Configuration dict
        """
        params = params or {}
        user_id = params.get('user_id', 'default')
        config_keys = params.get('config_keys', [])
        
        # Get user settings
        settings = self.settings_mgr.get_user_settings(user_id)
        
        if not settings:
            # Return defaults
            return {
                'sla_days': 30,
                'aging_buckets': [0, 30, 60, 90],
                'currency': 'INR',
                'date_format': 'YYYY-MM-DD',
                'reconciliation_tolerance': 0.01
            }
        
        # Extract requested configs
        if config_keys:
            config = {key: settings.get(key) for key in config_keys}
        else:
            # Return all relevant configs
            config = {
                'sla_days': settings.get('sla_days', 30),
                'aging_buckets': [0, 30, 60, 90],  # TODO: Make configurable
                'currency': settings.get('default_currency', 'INR'),
                'date_format': settings.get('date_format', 'YYYY-MM-DD'),
                'reconciliation_tolerance': 0.01,  # TODO: Make configurable
                'company_name': settings.get('company_name'),
                'primary_color': settings.get('primary_color')
            }
        
        self.logger.info(f"Fetched config for user: {user_id}")
        return config