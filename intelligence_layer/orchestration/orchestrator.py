"""
Orchestrator Agent - Uses User Settings (NO HARDCODING!)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from processing_layer.agents.core.base_agent import BaseAgent
from processing_layer.agents.ingestion_agent import IngestionAgent
from processing_layer.agents.extraction_agent import ExtractionAgent
from shared.llm.groq_client import get_groq_client
from shared.tools.mcp_financial_tools import PersistentFinancialMCPTools as FinancialMCPTools
from shared.calculations.calculation_engine import CalculationEngine, InvoiceCategory
from data_layer.schemas.canonical_schema import CanonicalFinancialDocument
from shared.tools.user_settings import get_settings_manager
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent - Uses User Settings for Everything
    """
    
    def __init__(self):
        super().__init__("OrchestratorAgent")
        
        # Initialize sub-agents
        self.ingestion_agent = IngestionAgent()
        self.groq = get_groq_client("accurate")
        self.extraction_agent = ExtractionAgent(self.groq)
        self.mcp_tools = FinancialMCPTools()
        
        from processing_layer.agents.calculation_coordinator_agent import CalculationCoordinatorAgent
        self.calc_coordinator = CalculationCoordinatorAgent(self.groq, self.mcp_tools)
        
        self.calc_engine = CalculationEngine()
        
        # User settings manager
        self.settings_mgr = get_settings_manager()
        
        self.documents_db = []
        
        self.logger.info("Orchestrator initialized with user settings system")
    
    def execute(self, state: dict) -> dict:
        """
        Execute orchestrator workflow (required by BaseLangGraphAgent)
        """
        action = state.get("action", "")
        
        if action == "upload":
            result = self.upload_document(
                state.get("file_path", ""),
                state.get("metadata", {})
            )
            state["upload_result"] = result
            
        elif action == "query":
            response = self.process_query(state.get("query", ""))
            state["query_response"] = response
            
        else:
            self.logger.warning(f"Unknown action: {action}")
        
        return state
    
    def upload_document(self, file_path: str, metadata: Dict = None) -> Dict[str, Any]:
        """Upload and process document"""
        self.logger.info(f"Processing: {Path(file_path).name}")
        
        try:
            # Get user ID
            user_id = metadata.get("company_id", "default") if metadata else "default"
            
            # Create state
            state = dict(
                file_path=file_path,
                company_id=user_id,
                input_data={},
                parsed_data={},
                canonical_data={},
                validation_errors=[],
                validation_warnings=[],
                is_valid=False,
                calculations={},
                report_type="",
                report_data={},
                report_path="",
                current_step="upload",
                workflow_id=f"upload-{datetime.now().timestamp()}",
                metadata=metadata or {},
                error_message=""
            )
            
            # Parse with Docling
            self.logger.info("→ Parsing with Docling...")
            state = self.ingestion_agent.execute(state)
            
            if state.get("error_message"):
                return {"status": "error", "error": state["error_message"]}
            
            self.logger.info("✓ Parsed")
            
            # Extract with LLM
            self.logger.info("→ Extracting with LLM...")
            state = self.extraction_agent.execute(state)
            
            if state.get("error_message"):
                return {"status": "error", "error": state["error_message"]}
            
            self.logger.info("✓ Extracted")
            
            # Calculate
            self.logger.info("→ Calculating...")
            canonical_doc = CanonicalFinancialDocument(**state["canonical_data"])
            canonical_doc = self.calc_engine.calculate_line_totals(canonical_doc)
            canonical_doc = self.calc_engine.calculate_document_totals(canonical_doc)
            
            # INTELLIGENT CATEGORIZATION
            if metadata and "category" in metadata:
                category = InvoiceCategory(metadata["category"])
                self.logger.info(f"✓ Explicit category: {category.value}")
            else:
                category = self._smart_categorize(canonical_doc, user_id)
            
            validation = self.calc_engine.validate_calculations(canonical_doc)
            
            self.logger.info(f"✓ Complete - Category: {category.value}")
            
            # Store
            doc_entry = {
                "id": len(self.documents_db) + 1,
                "file_path": file_path,
                "file_name": Path(file_path).name,
                "document": canonical_doc,
                "category": category.value,
                "validation": validation,
                "uploaded_at": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            self.documents_db.append(doc_entry)
            
            # Add to MCP tools
            document_data = {
                "company_id": user_id,
                "file_name": Path(file_path).name,
                "file_path": file_path,
                "document_number": canonical_doc.document_metadata.document_number,
                "document_date": canonical_doc.document_metadata.document_date,
                "category": category.value,
                "grand_total": canonical_doc.totals.grand_total,
                "tax_total": canonical_doc.totals.tax_total,
                "paid_amount": canonical_doc.totals.amount_paid,
                "parsed_data": state.get("parsed_data", {}),
                "canonical_data": state.get("canonical_data", {}),
                "document": canonical_doc,
            }

            self.mcp_tools.add_document(document_data)
            
            self.logger.info(f"✓ Stored - ID: {doc_entry['id']}")
            
            return {
                "status": "success",
                "document_id": doc_entry["id"],
                "document_number": canonical_doc.document_metadata.document_number,
                "category": category.value,
                "grand_total": canonical_doc.totals.grand_total,
                "validation": validation,
                "error": None
            }
            
        except Exception as e:
            self.logger.error(f"Upload failed: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "error": str(e)}
    
    def _smart_categorize(
        self,
        canonical_doc: CanonicalFinancialDocument,
        user_id: str
    ) -> InvoiceCategory:
        """
        Intelligent categorization using user settings
        """
        
        # Get company name from user settings
        our_company = self.settings_mgr.get_company_name(user_id)
        
        if not our_company:
            self.logger.warning(f"No company name for user: {user_id}, using AI")
            category = self.calc_coordinator.categorize_document(canonical_doc)
            self.logger.info(f"✓ AI category: {category.value}")
            return category
        
        # Normalize
        our_company = our_company.upper().strip()
        
        # Extract seller and buyer
        seller_name = ""
        if canonical_doc.seller and canonical_doc.seller.name:
            seller_name = canonical_doc.seller.name.upper().strip()
        
        buyer_name = ""
        if canonical_doc.buyer and canonical_doc.buyer.name:
            buyer_name = canonical_doc.buyer.name.upper().strip()
        
        self.logger.info(f"Comparing - Our: {our_company[:30]}, Seller: {seller_name[:30]}, Buyer: {buyer_name[:30]}")
        
        # Rule 1: We're the seller → SALES
        if our_company in seller_name or seller_name in our_company:
            self.logger.info(f"✓ SALES (we're seller): {our_company}")
            return InvoiceCategory.SALES
        
        # Rule 2: We're the buyer → PURCHASE
        if our_company in buyer_name or buyer_name in our_company:
            self.logger.info(f"✓ PURCHASE (we're buyer): {our_company}")
            return InvoiceCategory.PURCHASE
        
        # Rule 3: AI fallback
        self.logger.info("→ AI detection (company not found)")
        category = self.calc_coordinator.categorize_document(canonical_doc)
        self.logger.info(f"✓ AI category: {category.value}")
        return category
    
    def process_query(self, query: str) -> str:
        """Process user query"""
        self.logger.info(f"Processing query: {query}")
        
        try:
            state = dict(
                query=query,
                file_path="",
                company_id="",
                input_data={},
                parsed_data={},
                canonical_data={},
                validation_errors=[],
                validation_warnings=[],
                is_valid=True,
                calculations={},
                report_type="",
                report_data={},
                report_path="",
                current_step="query",
                workflow_id=f"query-{datetime.now().timestamp()}",
                metadata={},
                error_message=""
            )
            
            self.logger.info("→ Calculation Coordinator analyzing...")
            state = self.calc_coordinator.execute(state)
            
            if state.get("error_message"):
                return f"Sorry, I couldn't process your query: {state['error_message']}"
            
            response = state.get("formatted_response", "No response generated")
            
            self.logger.info(f"✓ Query processed - Report: {state.get('report_type')}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Query processing failed: {e}")
            return f"Sorry, an error occurred: {str(e)}"
    
    def get_document_list(self) -> List[Dict]:
        """Get list of all uploaded documents"""
        return [
            {
                "id": doc["id"],
                "file_name": doc["file_name"],
                "document_number": doc["document"].document_metadata.document_number,
                "category": doc["category"],
                "date": doc["document"].document_metadata.document_date,
                "amount": doc["document"].totals.grand_total,
                "uploaded_at": doc["uploaded_at"]
            }
            for doc in self.documents_db
        ]
    
    def get_document_by_id(self, doc_id: int) -> Optional[Dict]:
        """Get document by ID"""
        for doc in self.documents_db:
            if doc["id"] == doc_id:
                return doc
        return None
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status and statistics"""
        
        total_docs = len(self.documents_db)
        
        # Count by category
        sales_count = len([d for d in self.documents_db if d["category"] == "sales"])
        purchase_count = len([d for d in self.documents_db if d["category"] == "purchase"])
        
        # Calculate totals
        total_receivables = sum(
            d["document"].totals.balance_due or 0
            for d in self.documents_db
            if d["category"] == "sales"
        )
        
        total_payables = sum(
            d["document"].totals.balance_due or 0
            for d in self.documents_db
            if d["category"] == "purchase"
        )
        
        return {
            "status": "operational",
            "total_documents": total_docs,
            "sales_invoices": sales_count,
            "purchase_invoices": purchase_count,
            "total_receivables": total_receivables,
            "total_payables": total_payables,
            "last_upload": self.documents_db[-1]["uploaded_at"] if self.documents_db else None
        }


class FinancialAutomationSystem:
    """Financial Automation System"""
    
    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.logger = logger
        self.logger.info("Financial Automation System initialized")
    
    def upload(self, file_path: str, metadata: Dict = None) -> Dict[str, Any]:
        """Upload and process document"""
        return self.orchestrator.upload_document(file_path, metadata)
    
    async def process_document(self, file_path: str, metadata: Dict = None) -> Dict[str, Any]:
        """Process document (async wrapper for upload)"""
        return self.orchestrator.upload_document(file_path, metadata)
    
    def ask(self, question: str) -> str:
        """Ask question about financial data"""
        return self.orchestrator.process_query(question)
    
    def list_documents(self) -> List[Dict]:
        """Get list of all documents"""
        return self.orchestrator.get_document_list()
    
    def get_document(self, doc_id: int) -> Optional[Dict]:
        """Get specific document"""
        return self.orchestrator.get_document_by_id(doc_id)
    
    def status(self) -> Dict[str, Any]:
        """Get system status"""
        return self.orchestrator.get_system_status()