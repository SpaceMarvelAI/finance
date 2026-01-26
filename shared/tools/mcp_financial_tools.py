"""
Updated MCP Financial Tools - With Persistent Database
Replaces in-memory storage with SQLite database
"""

from typing import List, Dict, Any
from data_layer.database.database_manager import get_database
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class PersistentFinancialMCPTools:
    """
    Financial MCP Tools with Persistent Storage
    
    Uses SQLite database instead of in-memory list
    Data survives server restarts!
    """
    
    def __init__(self):
        self.db = get_database()
        logger.info("Persistent Financial MCP Tools initialized")
    
    @property
    def documents(self) -> List[Dict[str, Any]]:
        """
        Get all documents from database
        
        Returns documents in the same format as before
        for backward compatibility
        """
        db_docs = self.db.get_all_documents()
        
        # Convert to legacy format for compatibility
        legacy_docs = []
        for db_doc in db_docs:
            # Reconstruct the document object from canonical_data
            from data_layer.schemas.canonical_schema import CanonicalFinancialDocument
            
            canonical_dict = db_doc['canonical_data']
            
            # Create document object
            try:
                if canonical_dict:
                    document = CanonicalFinancialDocument(**canonical_dict)
                else:
                    # Fallback: create minimal document
                    document = None
            except:
                document = None
            
            # Legacy format
            legacy_doc = {
                "id": db_doc['id'],
                "company_id": db_doc['company_id'],
                "file_name": db_doc['file_name'],
                "document_number": db_doc['document_number'],
                "document_date": db_doc['document_date'],
                "category": db_doc['category'],
                "grand_total": db_doc['grand_total'],
                "tax_total": db_doc['tax_total'],
                "paid_amount": db_doc['paid_amount'],
                "outstanding": db_doc['outstanding'],
                "vendor_name": db_doc['vendor_name'],
                "customer_name": db_doc['customer_name'],
                "document": document,  # Canonical document object
                "uploaded_at": db_doc['uploaded_at']
            }
            
            legacy_docs.append(legacy_doc)
        
        return legacy_docs
    
    def add_document(self, document_data: Dict[str, Any]) -> int:
        """
        Add document to persistent database
        
        Args:
            document_data: Document data dictionary
            
        Returns:
            Document ID
        """
        doc_id = self.db.insert_document(document_data)
        logger.info(f"Document added to database: ID={doc_id}")
        return doc_id
    
    def get_purchase_invoices(self, company_id: str = None) -> List[Dict[str, Any]]:
        """Get all purchase invoices"""
        db_docs = self.db.get_documents_by_category("purchase", company_id)
        
        # Convert to legacy format
        legacy_docs = []
        for db_doc in db_docs:
            from data_layer.schemas.canonical_schema import CanonicalFinancialDocument
            
            canonical_dict = db_doc['canonical_data']
            
            try:
                document = CanonicalFinancialDocument(**canonical_dict) if canonical_dict else None
            except:
                document = None
            
            legacy_doc = {
                "id": db_doc['id'],
                "company_id": db_doc['company_id'],
                "file_name": db_doc['file_name'],
                "document_number": db_doc['document_number'],
                "category": db_doc['category'],
                "grand_total": db_doc['grand_total'],
                "document": document,
                "uploaded_at": db_doc['uploaded_at']
            }
            
            legacy_docs.append(legacy_doc)
        
        return legacy_docs
    
    def get_sales_invoices(self, company_id: str = None) -> List[Dict[str, Any]]:
        """Get all sales invoices"""
        db_docs = self.db.get_documents_by_category("sales", company_id)
        
        # Convert to legacy format (same as purchase_invoices)
        legacy_docs = []
        for db_doc in db_docs:
            from data_layer.schemas.canonical_schema import CanonicalFinancialDocument
            
            canonical_dict = db_doc['canonical_data']
            
            try:
                document = CanonicalFinancialDocument(**canonical_dict) if canonical_dict else None
            except:
                document = None
            
            legacy_doc = {
                "id": db_doc['id'],
                "company_id": db_doc['company_id'],
                "file_name": db_doc['file_name'],
                "document_number": db_doc['document_number'],
                "category": db_doc['category'],
                "grand_total": db_doc['grand_total'],
                "document": document,
                "uploaded_at": db_doc['uploaded_at']
            }
            
            legacy_docs.append(legacy_doc)
        
        return legacy_docs
    
    def get_statistics(self, company_id: str = None) -> Dict[str, Any]:
        """Get database statistics"""
        return self.db.get_statistics(company_id)
    
    def clear_all(self):
        """Clear all documents (admin function)"""
        logger.warning("Clearing all documents from database")
        # For now, we won't implement this to prevent accidental data loss
        pass