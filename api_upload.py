"""
Financial Automation API - Uses ONLY Existing Files
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import tempfile
import shutil
import sys

import sys
print('PYTHONPATH:', sys.path)

try:
    import data_layer.database.database_manager as dbm
    print('Loaded database_manager from:', dbm.__file__)
except Exception as e:
    print('Error importing database_manager:', e)
    
# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

app = FastAPI(
    title="Financial Automation API",
    description="Upload invoices and generate reports",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# MODELS
# ============================================================================

class QueryRequest(BaseModel):
    query: str
    company_id: str = "spacemarvel_001"


# ============================================================================
# 1. UPLOAD INVOICE
# ============================================================================

@app.post("/api/v1/upload")
async def upload_invoice(
    file: UploadFile = File(...),
    company_id: str = "spacemarvel_001"
):
    """
    Upload and process invoice
    
    Uses:
    - enhanced_ingestion_agent.py (parse with Docling)
    - database_manager.py (save to database)
    """
    import traceback
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name
        
        # Import what we actually have
        from processing_layer.document_processing.enhanced_ingestion_agent import EnhancedIngestionAgent
        from data_layer.database.database_manager import DatabaseManager
        
        # Parse with enhanced ingestion agent
        agent = EnhancedIngestionAgent()
        state = {'file_path': tmp_path}
        result = agent.execute(state)
        
        if result.get('error_message'):
            Path(tmp_path).unlink()
            raise HTTPException(status_code=400, detail=result['error_message'])
        
        # Get parsed data
        parsed_data = result.get('parsed_data', {})
        text = parsed_data.get('text', '')
        
        # Simple classification
        text_lower = text.lower()
        if any(w in text_lower for w in ['bill to', 'customer', 'sold to']):
            category = 'customer_invoice'
        else:
            category = 'vendor_invoice'
        
        # Save to database
        db = DatabaseManager()
        
        document_data = {
            'company_id': company_id,
            'file_name': file.filename,
            'file_path': tmp_path,
            'category': category,
            'parsed_data': parsed_data,
            'uploaded_at': datetime.now()
        }
        
        doc_id = db.insert_document(document_data)
        
        # Clean up
        Path(tmp_path).unlink()
        
        return {
            "status": "success",
            "document_id": doc_id,
            "category": category,
            "parsed_text_length": len(text),
            "message": " Invoice uploaded and saved to database"
        }
        
    except Exception as e:
        # Clean up on error
        if 'tmp_path' in locals() and Path(tmp_path).exists():
            Path(tmp_path).unlink()
        
        # Return full traceback
        tb = traceback.format_exc()
        raise HTTPException(
            status_code=500, 
            detail={
                "error": str(e),
                "traceback": tb
            }
        )


# ============================================================================
# 2. QUERY AND GENERATE REPORT
# ============================================================================

@app.post("/api/v1/query")
async def process_query(request: QueryRequest):
    """
    Process natural language query and generate report
    
    Uses:
    - enhanced_orchestrator.py (main orchestrator)
    - enhanced_intent_parser.py (parse query)
    - domain_classifier.py (classify domain)
    - variable_extractor.py (extract variables)
    - All agents (ap_aging_agent.py, ar_aging_agent.py, etc.)
    - All nodes (data_nodes.py, calculation_nodes.py, etc.)
    - branded_excel_generator.py (generate report)
    """
    try:
        from intelligence_layer.orchestration.enhanced_orchestrator import EnhancedOrchestrator
        
        orchestrator = EnhancedOrchestrator()
        result = orchestrator.execute(
            request.query,
            context={"company_id": request.company_id}
        )
        
        if result.get('status') == 'success':
            return {
                "status": "success",
                "domain": result.get('domain'),
                "report_type": result.get('report_type'),
                "report_path": result.get('report_path'),
                "execution_time": result.get('execution_time'),
                "message": " Report generated successfully"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get('error', 'Query processing failed')
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# 3. HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# ============================================================================
# 4. LIST DOCUMENTS
# ============================================================================

@app.get("/api/v1/documents")
async def list_documents(company_id: str = "spacemarvel_001"):
    """List all uploaded documents"""
    try:
        from data_layer.database.database_manager import DatabaseManager
        
        db = DatabaseManager()
        documents = db.get_all_documents(company_id)
        
        return {
            "status": "success",
            "total": len(documents),
            "documents": documents[:10]  # Return first 10
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

