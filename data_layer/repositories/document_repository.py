"""
Document Repository
Data access layer for document operations
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from data_layer.models.database_models import Document, Company
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class DocumentRepository:
    """Repository for document database operations"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create_document(
        self,
        company_id: str,
        file_name: str,
        file_path: str,
        file_type: str,
        file_size: int,
        canonical_data: Dict[str, Any]
    ) -> Document:
        """
        Create a new document record
        
        Args:
            company_id: Company/tenant ID
            file_name: Original file name
            file_path: Storage path
            file_type: File extension (pdf, xlsx, csv, docx)
            file_size: File size in bytes
            canonical_data: Extracted canonical JSON
            
        Returns:
            Created Document object
        """
        try:
            document = Document(
                company_id=company_id,
                file_name=file_name,
                file_path=file_path,
                file_type=file_type,
                file_size=file_size,
                canonical_data=canonical_data,
                document_type=canonical_data.get("document_metadata", {}).get("document_type"),
                document_number=canonical_data.get("document_metadata", {}).get("document_number"),
                document_date=canonical_data.get("document_metadata", {}).get("document_date"),
                status="completed",
                processed_at=datetime.utcnow()
            )
            
            self.session.add(document)
            self.session.flush()  # Get the ID without committing
            
            logger.info(f"Document created: {document.id}")
            return document
            
        except Exception as e:
            logger.error(f"Error creating document: {str(e)}")
            raise
    
    def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """Get document by ID"""
        return self.session.query(Document).filter(Document.id == document_id).first()
    
    def get_documents_by_company(
        self,
        company_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Document]:
        """Get all documents for a company"""
        return (
            self.session.query(Document)
            .filter(Document.company_id == company_id)
            .order_by(Document.uploaded_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
    
    def get_documents_by_type(
        self,
        company_id: str,
        document_type: str
    ) -> List[Document]:
        """Get documents filtered by type"""
        return (
            self.session.query(Document)
            .filter(
                Document.company_id == company_id,
                Document.document_type == document_type
            )
            .order_by(Document.uploaded_at.desc())
            .all()
        )
    
    def update_document_status(
        self,
        document_id: str,
        status: str,
        errors: Optional[str] = None
    ) -> bool:
        """Update document processing status"""
        try:
            document = self.get_document_by_id(document_id)
            if document:
                document.status = status
                if errors:
                    document.processing_errors = errors
                document.processed_at = datetime.utcnow()
                self.session.flush()
                logger.info(f"Document {document_id} status updated to {status}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating document status: {str(e)}")
            raise
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document"""
        try:
            document = self.get_document_by_id(document_id)
            if document:
                self.session.delete(document)
                self.session.flush()
                logger.info(f"Document deleted: {document_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise
    
    def get_document_count_by_company(self, company_id: str) -> int:
        """Get total document count for a company"""
        return (
            self.session.query(Document)
            .filter(Document.company_id == company_id)
            .count()
        )
    
    def search_documents(
        self,
        company_id: str,
        search_term: str,
        limit: int = 50
    ) -> List[Document]:
        """Search documents by file name or document number"""
        return (
            self.session.query(Document)
            .filter(
                Document.company_id == company_id,
                (Document.file_name.ilike(f"%{search_term}%")) |
                (Document.document_number.ilike(f"%{search_term}%"))
            )
            .limit(limit)
            .all()
        )