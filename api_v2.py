"""
API v2 - Enhanced API with LangGraph Integration
Updated API endpoints that use the new LangGraph framework and ReportTemplateIntegration
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timedelta
import uuid
import os
import sys
import shutil
try:
    import jwt  # PyJWT
except ImportError:
    print("ERROR: PyJWT not installed. Run: pip install PyJWT")
    sys.exit(1)
import bcrypt

sys.path.insert(0, os.getcwd())

# Import LangGraph integration
from processing_layer.agents.langgraph_framework.report_template_integration import ReportTemplateIntegration
from processing_layer.agents.langgraph_framework.workflow_builder import WorkflowBuilder
from processing_layer.agents.langgraph_framework.agent_orchestrator import AgentOrchestrator

# Import existing components
from processing_layer.document_processing.document_processing_service import DocumentProcessingService
from processing_layer.document_processing.parsers.universal_docling_parser import UniversalDoclingParser
from processing_layer.document_processing.parsers.csv_parser import CSVParser
from intelligence_layer.routing.router_prompt_integrator import RouterPromptIntegrator
from intelligence_layer.parsing.enhanced_intent_parser import EnhancedIntentParser
from intelligence_layer.orchestration.workflow_planner_agent import WorkflowPlannerAgent
from processing_layer.agents.accounts_payable.ap_aging_agent import APAgingAgent
from processing_layer.agents.accounts_payable.ap_register_agent import APRegisterAgent
from processing_layer.agents.accounts_payable.ap_overdue_agent import APOverdueAgent
from processing_layer.agents.accounts_payable.ap_duplicate_agent import APDuplicateAgent
from processing_layer.agents.accounts_receivable.ar_aging_agent import ARAgingAgent
from processing_layer.agents.accounts_receivable.ar_register_agent import ARRegisterAgent
from processing_layer.agents.accounts_receivable.ar_collection_agent import ARCollectionAgent
from processing_layer.agents.accounts_receivable.dso_agent import DSOAgent
from processing_layer.workflows.nodes.base_node import NodeRegistry
from data_layer.database.database_manager import get_database
from shared.llm.groq_client import get_groq_client
from shared.config.logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# DATABASE MODELS - EXACT MATCH TO YOUR SCHEMA
# ============================================================================

from sqlalchemy import create_engine, Column, String, DateTime, Integer, Boolean, Text, Numeric
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import QueuePool

Base = declarative_base()

class User(Base):
    """Matches: public.users"""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    company_id = Column(String(36), nullable=False)
    is_active = Column(Boolean)
    created_at = Column(DateTime)
    last_login = Column(DateTime)

class Company(Base):
    """Matches: public.companies"""
    __tablename__ = "companies"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    tax_id = Column(String(50))
    registration_number = Column(String(50))
    email = Column(String(255))
    phone = Column(String(50))
    website = Column(String(255))
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    logo_url = Column(String(500))
    company_aliases = Column(ARRAY(Text), nullable=True)
    primary_color = Column(String(7), default='#1976D2')
    secondary_color = Column(String(7), default='#424242')
    currency = Column(String(3), default='INR')
    fiscal_year_start = Column(String(5))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class Document(Base):
    """Matches: public.documents"""
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True)
    company_id = Column(String(36), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500))
    file_type = Column(String(10))
    file_size = Column(Integer)
    document_type = Column(String(50))
    document_number = Column(String(100))
    document_date = Column(DateTime)
    category = Column(String(50))
    docling_parsed_data = Column(JSONB)
    canonical_data = Column(JSONB)
    status = Column(String(50), default='pending')
    confidence_score = Column(Numeric(3, 2))
    vendor_name = Column(String(255))
    customer_name = Column(String(255))
    grand_total = Column(Numeric(15, 2), default=0.0)
    tax_total = Column(Numeric(15, 2), default=0.0)
    paid_amount = Column(Numeric(15, 2), default=0.0)
    outstanding = Column(Numeric(15, 2), default=0.0)
    uploaded_at = Column(DateTime)
    parsed_at = Column(DateTime)
    processed_at = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class Workflow(Base):
    """Matches: public.workflows"""
    __tablename__ = "workflows"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default='planned')
    company_id = Column(String(50), nullable=False)
    user_id = Column(String(50), nullable=False)
    query = Column(Text)
    domain = Column(String(50))
    report_type = Column(String(100))
    workflow_definition = Column(JSONB, nullable=False)
    execution_result = Column(JSONB)
    created_at = Column(DateTime, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    output_file_path = Column(String(500))
    execution_time_ms = Column(Integer)
    error_message = Column(Text)

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/financial_automation")
    UPLOAD_DIR = Path("./data/uploads")
    OUTPUT_DIR = Path("./output/reports")
    API_HOST = "0.0.0.0"
    API_PORT = 8001  # Different port for v2
    JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    TOKEN_EXPIRE_HOURS = 24

config = Config()
config.UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
config.OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# ============================================================================
# DATABASE
# ============================================================================

engine = create_engine(config.DATABASE_URL, poolclass=QueuePool, pool_size=10)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================================================
# INITIALIZE SERVICES
# ============================================================================

db_manager = get_database()
docling_parser = UniversalDoclingParser()
csv_parser = CSVParser()
llm_client = get_groq_client("accurate")
router = RouterPromptIntegrator()
intent_parser = EnhancedIntentParser(llm_client=llm_client)
workflow_planner = WorkflowPlannerAgent(llm_client=llm_client)

# Initialize LangGraph Integration
report_integration = ReportTemplateIntegration()
workflow_builder = WorkflowBuilder()
agent_orchestrator = AgentOrchestrator()

AGENTS = {
    'ap_aging': APAgingAgent(),
    'ap_register': APRegisterAgent(),
    'ap_overdue': APOverdueAgent(),
    'ap_duplicate': APDuplicateAgent(),
    'ar_aging': ARAgingAgent(),
    'ar_register': ARRegisterAgent(),
    'ar_collection': ARCollectionAgent(),
    'dso': DSOAgent()
}

logger.info(f" System initialized with {len(AGENTS)} agents and LangGraph integration")

# ============================================================================
# SECURITY
# ============================================================================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.utcnow() + timedelta(hours=config.TOKEN_EXPIRE_HOURS)}
    return jwt.encode(payload, config.JWT_SECRET, algorithm="HS256")

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"])
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(authorization: str = Header(...), db: Session = Depends(get_db)) -> User:
    token = authorization.replace("Bearer ", "")
    payload = decode_token(token)
    user = db.query(User).filter(User.id == payload['sub']).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# ============================================================================
# MODELS
# ============================================================================

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ChatQuery(BaseModel):
    query: str

class ReportGenerationRequest(BaseModel):
    template_type: str
    report_data: Dict[str, Any]
    company_id: str
    params: Optional[Dict[str, Any]] = None

class WorkflowExecutionRequest(BaseModel):
    template_type: str
    report_data: Dict[str, Any]
    company_id: str
    user_id: str
    session_id: Optional[str] = None

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(title="Financial Automation System - API v2", version="2.0.0", docs_url="/docs/v2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Mount static files directory
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="./data"), name="static")

# ============================================================================
# ENHANCED ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {
        "service": "Financial Automation System - API v2",
        "version": "2.0.0",
        "status": "operational",
        "features": {
            "agents": len(AGENTS),
            "nodes": len(NodeRegistry.get_all_nodes()),
            "langgraph_integration": True,
            "report_templates": len(report_integration.get_available_templates())
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "agents": len(AGENTS),
        "nodes": len(NodeRegistry.get_all_nodes()),
        "langgraph_integration": True,
        "report_templates": len(report_integration.get_available_templates())
    }

# ============================================================================
# AUTHENTICATION ENDPOINTS (Same as v1)
# ============================================================================

@app.post("/api/v2/auth/register")
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register new user"""
    
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    company_id = str(uuid.uuid4())
    
    # Create company
    company = Company(
        id=company_id,
        name=user_data.company_name,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Create user
    user = User(
        id=user_id,
        company_id=company_id,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        full_name=user_data.full_name,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    db.add(company)
    db.add(user)
    db.commit()
    
    token = create_token(user_id)
    
    logger.info(f" User registered: {user_data.email} - {user_data.company_name}")
    
    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "user_id": user_id,
        "company_id": company_id,
        "company_name": user_data.company_name
    }

@app.post("/api/v2/auth/login")
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login"""
    
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user.id)
    company = db.query(Company).filter(Company.id == user.company_id).first()
    
    return {
        "status": "success",
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "company_id": user.company_id,
        "company_name": company.name if company else "Unknown"
    }

# ============================================================================
# DOCUMENT PROCESSING (Enhanced with LangGraph)
# ============================================================================

@app.post("/api/v2/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload invoice with enhanced processing"""
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        filepath = config.UPLOAD_DIR / filename
        
        with filepath.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        company = db.query(Company).filter(Company.id == current_user.company_id).first()
        
        file_ext = Path(file.filename).suffix.lower()
        parser = csv_parser if file_ext == '.csv' else docling_parser
        
        # Enhanced processor with LangGraph integration
        processor = DocumentProcessingService(
            db_session=db_manager,
            docling_parser=parser,
            company_id=current_user.company_id,
            user_company_name=company.name
        )
        
        result = processor.process_upload(
            file_path=str(filepath),
            file_name=file.filename
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail="Processing failed")
        
        logger.info(f" Document processed: {result['document_id']}")
        
        return {
            "status": "success",
            "document_id": result['document_id'],
            "category": result.get('invoice_category'),
            "party": result.get('party_info'),
            "extracted_data": result.get('extracted_data'),
            "processing_time": result.get('processing_time'),
            "confidence_score": result.get('confidence_score')
        }
        
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v2/documents")
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 100
):
    """List uploaded documents"""
    
    documents = db.query(Document).filter(
        Document.company_id == current_user.company_id
    ).order_by(Document.uploaded_at.desc()).limit(limit).all()
    
    return {
        "status": "success",
        "count": len(documents),
        "documents": [
            {
                "id": doc.id,
                "file_name": doc.file_name,
                "document_type": doc.document_type,
                "category": doc.category,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                "status": doc.status,
                "confidence_score": float(doc.confidence_score) if doc.confidence_score else None,
                "party_info": {
                    "vendor_name": doc.vendor_name,
                    "customer_name": doc.customer_name
                },
                "amounts": {
                    "grand_total": float(doc.grand_total) if doc.grand_total else None,
                    "tax_total": float(doc.tax_total) if doc.tax_total else None,
                    "outstanding": float(doc.outstanding) if doc.outstanding else None
                }
            }
            for doc in documents
        ]
    }

# ============================================================================
# REPORT GENERATION (New - Using LangGraph Integration)
# ============================================================================

@app.get("/api/v2/reports/templates")
async def get_report_templates():
    """Get available report templates"""
    
    try:
        templates = report_integration.get_available_templates()
        capabilities = report_integration.get_template_capabilities()
        
        return {
            "status": "success",
            "templates": templates,
            "capabilities": capabilities,
            "count": len(templates)
        }
        
    except Exception as e:
        logger.error(f"Failed to get templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v2/reports/templates/{template_type}")
async def get_template_info(template_type: str):
    """Get detailed template information"""
    
    try:
        template_info = report_integration.get_template_info(template_type)
        
        return {
            "status": "success",
            "template_type": template_type,
            "info": template_info
        }
        
    except Exception as e:
        logger.error(f"Failed to get template info: {e}")
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/v2/reports/generate")
async def generate_report(
    request: ReportGenerationRequest,
    current_user: User = Depends(get_current_user)
):
    """Generate report using LangGraph integration"""
    
    try:
        # Validate inputs
        if request.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Generate report using LangGraph integration
        result = report_integration.generate_report(
            template_type=request.template_type,
            report_data=request.report_data,
            company_id=request.company_id,
            params=request.params or {}
        )
        
        if result['status'] != 'success':
            raise HTTPException(status_code=500, detail=result.get('error', 'Report generation failed'))
        
        logger.info(f" Report generated: {result['file_path']}")
        
        return {
            "status": "success",
            "file_path": result['file_path'],
            "download_url": f"/api/v2/reports/download/{Path(result['file_path']).name}",
            "branding_applied": result.get('branding_applied', False),
            "report_type": result.get('report_type'),
            "generation_time": result.get('generation_time')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v2/reports/workflow")
async def execute_report_workflow(
    request: WorkflowExecutionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute report generation workflow with LangGraph"""
    
    try:
        # Validate inputs
        if request.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if request.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Create workflow record
        workflow_id = str(uuid.uuid4())
        workflow = Workflow(
            id=workflow_id,
            name=f"{request.template_type.upper()} Report",
            type=request.template_type,
            status='executing',
            company_id=request.company_id,
            user_id=request.user_id,
            query=f"Generate {request.template_type} report",
            domain='APLayer' if request.template_type.startswith('ap_') else 'ARLayer',
            report_type=request.template_type,
            workflow_definition={},
            created_at=datetime.utcnow(),
            started_at=datetime.utcnow()
        )
        
        db.add(workflow)
        db.commit()
        
        # Execute workflow using LangGraph
        result = report_integration.execute_report_workflow(
            template_type=request.template_type,
            report_data=request.report_data,
            company_id=request.company_id,
            params=request.params or {},
            session_id=request.session_id or workflow_id
        )
        
        # Update workflow record
        if result['status'] == 'success':
            workflow.status = 'completed'
            workflow.completed_at = datetime.utcnow()
            workflow.execution_time_ms = result.get('execution_time_ms', 0)
            workflow.output_file_path = result.get('file_path')
            workflow.execution_result = result
        else:
            workflow.status = 'failed'
            workflow.error_message = result.get('error', 'Workflow execution failed')
        
        db.commit()
        
        if result['status'] != 'success':
            raise HTTPException(status_code=500, detail=result.get('error', 'Workflow execution failed'))
        
        logger.info(f" Workflow executed: {workflow_id}")
        
        return {
            "status": "success",
            "workflow_id": workflow_id,
            "file_path": result['file_path'],
            "download_url": f"/api/v2/reports/download/{Path(result['file_path']).name}",
            "execution_time_ms": result.get('execution_time_ms'),
            "template_type": result.get('template_type'),
            "session_id": result.get('session_id')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v2/reports")
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """List generated reports"""
    
    workflows = db.query(Workflow).filter(
        Workflow.company_id == current_user.company_id
    ).order_by(Workflow.created_at.desc()).limit(limit).all()
    
    return {
        "status": "success",
        "count": len(workflows),
        "reports": [
            {
                "id": wf.id,
                "name": wf.name,
                "type": wf.type,
                "status": wf.status,
                "created_at": wf.created_at.isoformat(),
                "completed_at": wf.completed_at.isoformat() if wf.completed_at else None,
                "execution_time_ms": wf.execution_time_ms,
                "output_file": wf.output_file_path,
                "error_message": wf.error_message
            }
            for wf in workflows
        ]
    }

@app.get("/api/v2/reports/download/{filename}")
async def download_report(filename: str):
    """Download report"""
    file_path = config.OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)

# ============================================================================
# SYSTEM STATUS AND MONITORING
# ============================================================================

@app.get("/api/v2/system/status")
async def system_status():
    """Get comprehensive system status"""
    
    try:
        # Get system information
        templates = report_integration.get_available_templates()
        capabilities = report_integration.get_template_capabilities()
        
        # Get node information
        nodes = NodeRegistry.get_all_nodes()
        
        # Get agent information
        agent_info = {key: agent.__class__.__name__ for key, agent in AGENTS.items()}
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "report_templates": {
                    "count": len(templates),
                    "available": templates,
                    "capabilities": capabilities
                },
                "workflow_nodes": {
                    "count": len(nodes),
                    "nodes": nodes
                },
                "agents": {
                    "count": len(AGENTS),
                    "agents": agent_info
                }
            },
            "integration": {
                "langgraph": True,
                "report_templates": True,
                "workflow_builder": True,
                "agent_orchestrator": True
            }
        }
        
    except Exception as e:
        logger.error(f"System status check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/api/v2/system/metrics")
async def system_metrics():
    """Get system performance metrics"""
    
    try:
        # Get report statistics
        reports_dir = Path(config.OUTPUT_DIR)
        if reports_dir.exists():
            report_files = list(reports_dir.glob("*.xlsx"))
            total_reports = len(report_files)
            total_size = sum(f.stat().st_size for f in report_files)
        else:
            total_reports = 0
            total_size = 0
        
        return {
            "status": "success",
            "metrics": {
                "reports": {
                    "total_generated": total_reports,
                    "total_size_bytes": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2)
                },
                "templates": {
                    "available": len(report_integration.get_available_templates())
                },
                "nodes": {
                    "registered": len(NodeRegistry.get_all_nodes())
                },
                "agents": {
                    "available": len(AGENTS)
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "=" * 80)
    print("🚀 FINANCIAL AUTOMATION SYSTEM - API v2")
    print("   Enhanced with LangGraph Integration")
    print("=" * 80)
    print(f"\n🌐 Server: http://{config.API_HOST}:{config.API_PORT}")
    print(f"📖 Docs:   http://{config.API_HOST}:{config.API_PORT}/docs/v2\n")
    print("✨ New Features:")
    print("   • LangGraph workflow integration")
    print("   • Enhanced report generation")
    print("   • Workflow execution tracking")
    print("   • System status monitoring")
    print("   • Performance metrics")
    print("=" * 80 + "\n")
    
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT, reload=False)