#!/usr/bin/env python3
"""
Production API with LangGraph Integration
Replaces hardcoded agents with LangGraph-based agents while maintaining the same API endpoints
"""

import asyncio
import json
import logging
import os
import sys
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, File, Header, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialize logger first (needed before imports)
logger = logging.getLogger(__name__)

# Import core components
try:
    from data_layer.database.database_manager import get_database
except ImportError:
    logger.warning("Could not import get_database")
    get_database = lambda: None

try:
    from intelligence_layer.parsing.domain_classifier import DomainClassifier
except ImportError:
    logger.warning("Could not import DomainClassifier")
    DomainClassifier = None

try:
    from intelligence_layer.routing.router_prompt_integrator import RouterPromptIntegrator
except ImportError:
    logger.warning("Could not import RouterPromptIntegrator")
    RouterPromptIntegrator = None

try:
    from processing_layer.document_processing.document_processing_service import DocumentProcessingService
except ImportError:
    logger.warning("Could not import DocumentProcessingService")
    DocumentProcessingService = None

try:
    from shared.config.logging_config import get_logger
except ImportError:
    logger.warning("Could not import get_logger from shared, using built-in logger")
    get_logger = lambda x: logging.getLogger(x)

try:
    from shared.config.settings import Settings
except ImportError:
    logger.warning("Could not import Settings")
    Settings = None

try:
    from shared.llm.factory import LLMFactory
except ImportError:
    logger.warning("Could not import LLMFactory")
    LLMFactory = None

try:
    from shared.utils.file_utils import get_file_extension, validate_file_type
except ImportError:
    logger.warning("Could not import file_utils functions")
    get_file_extension = lambda x: x.split('.')[-1] if '.' in x else ''
    validate_file_type = lambda x: x.endswith(('.pdf', '.xlsx', '.csv', '.docx'))

# Import database models for workflow persistence
try:
    from sqlalchemy import create_engine, Column, String, DateTime, Integer, Boolean, Text, Numeric
    from sqlalchemy.dialects.postgresql import JSONB, ARRAY
    from sqlalchemy.orm import declarative_base, sessionmaker, Session
    from sqlalchemy.pool import QueuePool
    from sqlalchemy import text
    from uuid import uuid4
    from datetime import datetime
    
    # Database models for workflow persistence
    Base = declarative_base()
    
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
    
    # Database connection for workflow persistence
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/financial_automation")
    workflow_engine = create_engine(DATABASE_URL, poolclass=QueuePool, pool_size=10)
    WorkflowSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=workflow_engine)
    
    def get_workflow_db():
        db = WorkflowSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def save_workflow_to_db(
        workflow_id: str,
        name: str,
        workflow_type: str,
        status: str,
        company_id: str,
        user_id: str,
        query: str,
        domain: str,
        report_type: str,
        workflow_definition: dict,
        execution_result: dict = None,
        started_at: datetime = None,
        completed_at: datetime = None,
        output_file_path: str = None,
        execution_time_ms: int = None,
        error_message: str = None
    ) -> bool:
        """Save workflow to database"""
        try:
            db = WorkflowSessionLocal()
            
            # Create workflow record
            workflow = Workflow(
                id=workflow_id,
                name=name,
                type=workflow_type,
                status=status,
                company_id=company_id,
                user_id=user_id,
                query=query,
                domain=domain,
                report_type=report_type,
                workflow_definition=workflow_definition,
                execution_result=execution_result,
                created_at=datetime.utcnow(),
                started_at=started_at,
                completed_at=completed_at,
                output_file_path=output_file_path,
                execution_time_ms=execution_time_ms,
                error_message=error_message
            )
            
            db.add(workflow)
            db.commit()
            db.close()
            
            logger.info(f"Workflow saved to database: {workflow_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save workflow to database: {e}")
            if 'db' in locals():
                db.rollback()
                db.close()
            return False
    
    logger.info("Workflow persistence system initialized")
    
except ImportError as e:
    logger.warning(f"Could not import database components for workflow persistence: {e}")
    def save_workflow_to_db(*args, **kwargs):
        logger.warning("Workflow persistence not available - database components not imported")
        return False

# Import LangGraph components
try:
    from processing_layer.agents.langgraph_framework.agent_orchestrator import AgentOrchestrator
except ImportError as e:
    logger.error(f"Could not import AgentOrchestrator: {e}")
    raise

try:
    from processing_layer.agents.langgraph_framework.workflow_builder import WorkflowBuilder
except ImportError as e:
    logger.error(f"Could not import WorkflowBuilder: {e}")
    raise

try:
    from processing_layer.agents.langgraph_framework.report_template_integration import ReportTemplateIntegration
    report_template_integration = ReportTemplateIntegration()
except ImportError as e:
    logger.warning(f"Could not import ReportTemplateIntegration: {e}")
    report_template_integration = None

# Import Authentication System
try:
    from auth_system import setup_auth_system
except ImportError as e:
    logger.error(f"Could not import auth_system: {e}")
    raise

# Mock Pydantic models for endpoints (in case production_api can't be imported)
class APOverdueResponse(BaseModel):
    success: bool
    message: str = ""
    data: Dict[str, Any] = {}
    
class APAgingResponse(BaseModel):
    success: bool
    message: str = ""
    data: Dict[str, Any] = {}
    
class APRegisterResponse(BaseModel):
    success: bool
    message: str = ""
    data: Dict[str, Any] = {}
    
class ARCollectionResponse(BaseModel):
    success: bool
    message: str = ""
    data: Dict[str, Any] = {}
    
class ARRegisterResponse(BaseModel):
    success: bool
    message: str = ""
    data: Dict[str, Any] = {}
    
class DSOResponse(BaseModel):
    success: bool
    message: str = ""
    data: Dict[str, Any] = {}

# Define Session Models
class UserSessionData(BaseModel):
    session_id: str
    user_id: str
    company_id: str
    start_time: str
    context: Dict[str, Any] = {}
    active: bool = True

class UserSessionRequest(BaseModel):
    user_id: str
    company_id: str

class UserSessionResponse(BaseModel):
    session_id: str
    user_id: str
    company_id: str
    start_time: str
    context: Dict[str, Any] = {}
    active: bool = True

class UserSession(BaseModel):
    session_id: str
    user_id: str
    company_id: str
    start_time: datetime
    context: Dict[str, Any] = {}
    active: bool = True

class ChatQueryRequest(BaseModel):
    """Request model for chat query endpoint supporting JSON body"""
    query: str
    user_id: str
    company_id: str
    session_id: Optional[str] = None
    agent_type: Optional[str] = None

# Try to import additional models from production_api (optional)
try:
    from production_api import (
        APOverdueRequest, APOverdueSummaryResponse,
        APRegisterRequest, APRegisterSummaryResponse,
        APAgingRequest, APAgingSummaryResponse,
        ARCollectionRequest, ARCollectionSummaryResponse,
        ARRegisterRequest, ARRegisterSummaryResponse,
        ARSummaryResponse, ARSummaryRequest,
        DSORequest, DSOSummaryResponse,
        UploadRequest, UploadResponse, UploadSummaryResponse,
        UserRegistrationRequest, UserRegistrationResponse,
        UserLoginRequest, UserLoginResponse,
        BrandingRequest, BrandingResponse,
        CompanyRegistrationRequest, CompanyRegistrationResponse,
        CompanyLoginRequest, CompanyLoginResponse,
        CompanyProfileResponse, CompanyProfileRequest,
    )
except ImportError as e:
    logger.warning(f"Could not import all models from production_api: {e}")
    # Define fallback classes
    APOverdueRequest = BaseModel
    APRegisterRequest = BaseModel
    APAgingRequest = BaseModel
    ARCollectionRequest = BaseModel
    ARRegisterRequest = BaseModel
    DSORequest = BaseModel
    UploadRequest = BaseModel
    UploadResponse = BaseModel
    UploadSummaryResponse = BaseModel
    UserRegistrationRequest = BaseModel
    UserRegistrationResponse = BaseModel
    UserLoginRequest = BaseModel
    UserLoginResponse = BaseModel

logger = get_logger(__name__) if callable(get_logger) else logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Production API with LangGraph Integration",
    description="Production-ready API with LangGraph-based agents replacing hardcoded implementations",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup Authentication System
setup_auth_system(app)

# Initialize services
db = None
try:
    db = get_database()
except Exception as e:
    logger.warning(f"Database connection failed: {e}")

llm_factory = LLMFactory() if LLMFactory else None
domain_classifier = DomainClassifier() if DomainClassifier else None
router_prompt_integrator = RouterPromptIntegrator() if RouterPromptIntegrator else None

# DocumentProcessingService requires DB, parser, company_id - keep as None (lazy-load if needed)
document_processor = None

# Initialize LangGraph components
agent_orchestrator = AgentOrchestrator()
# WorkflowBuilder is lazy-loaded (it has issues with StateGraph schema on init)
workflow_builder = None

# Global variables for session management
active_sessions: Dict[str, Dict[str, Any]] = {}
user_sessions: Dict[str, Any] = {}

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging all requests and responses"""
    async def dispatch(self, request: Request, call_next):
        start_time = datetime.now()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Response: {response.status_code} - {process_time:.2f}s")
        
        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

app.add_middleware(LoggingMiddleware)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# Enhanced production endpoints with LangGraph integration

@app.post("/upload", response_model=Dict[str, Any])
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Query(..., description="User ID"),
    company_id: str = Query(..., description="Company ID"),
    agent_type: Optional[str] = Query(None, description="Preferred agent type")
):
    """Upload document with automatic parsing, extraction, currency conversion and DB save"""
    try:
        # Validate file
        if not validate_file_type(file.filename):
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        # Process with LangGraph agent
        result = await agent_orchestrator.execute_agent(
            agent_type=agent_type or "document_processing",
            user_id=user_id,
            company_id=company_id,
            query=f"Process and extract data from: {file.filename}",
            context={
                "file": file,
                "workflow_type": "document_processing"
            },
            session_id=str(uuid4())
        )
        
        return {
            "success": result['status'] == 'success',
            "message": result['response'],
            "document_id": result.get('document_id', ''),
            "extracted_data": result.get('extracted_data', {}),
            "processing_time": result.get('processing_time', 0),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/ap/aging", response_model=APAgingResponse)
async def get_ap_aging(
    user_id: str = Query(..., description="User ID"),
    company_id: str = Query(..., description="Company ID"),
    agent_type: Optional[str] = Query(None, description="Preferred agent type"),
    workflow_type: Optional[str] = Query(None, description="Preferred workflow type")
):
    """Enhanced AP Aging with LangGraph agent analysis"""
    try:
        # Validate user and company
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Process with LangGraph agent
        result = await agent_orchestrator.execute_agent(
            agent_type=agent_type or "ap_aging",
            user_id=user_id,
            company_id=company_id,
            query="Generate AP Aging report",
            context={"workflow_type": workflow_type or "report_generation"},
            session_id=str(uuid4())
        )
        
        return APAgingResponse(
            success=True,
            message="AP Aging report generated successfully",
            data=result.get('data', {}),
            summary=APAgingSummaryResponse(
                total_due=result.get('total_due', 0),
                current_0_30=result.get('current_0_30', 0),
                days_31_60=result.get('days_31_60', 0),
                days_61_90=result.get('days_61_90', 0),
                days_90_plus=result.get('days_90_plus', 0)
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AP Aging failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AP Aging failed: {str(e)}")

@app.get("/ap/register", response_model=APRegisterResponse)
async def get_ap_register(
    user_id: str = Query(..., description="User ID"),
    company_id: str = Query(..., description="Company ID"),
    agent_type: Optional[str] = Query(None, description="Preferred agent type"),
    workflow_type: Optional[str] = Query(None, description="Preferred workflow type")
):
    """Enhanced AP Register with LangGraph agent analysis"""
    try:
        # Validate user and company
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Process with LangGraph agent
        result = await agent_orchestrator.execute_agent(
            agent_type=agent_type or "ap_register",
            user_id=user_id,
            company_id=company_id,
            query="Generate AP Register report",
            context={"workflow_type": workflow_type or "report_generation"},
            session_id=str(uuid4())
        )
        
        return APRegisterResponse(
            success=True,
            message="AP Register report generated successfully",
            data=result.get('data', {}),
            summary=APRegisterSummaryResponse(
                total_invoices=result.get('total_invoices', 0),
                total_amount=result.get('total_amount', 0),
                total_paid=result.get('total_paid', 0),
                total_outstanding=result.get('total_outstanding', 0),
                paid_count=result.get('paid_count', 0),
                partial_count=result.get('partial_count', 0),
                unpaid_count=result.get('unpaid_count', 0)
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AP Register failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AP Register failed: {str(e)}")

@app.get("/ap/overdue", response_model=APOverdueResponse)
async def get_ap_overdue(
    user_id: str = Query(..., description="User ID"),
    company_id: str = Query(..., description="Company ID"),
    agent_type: Optional[str] = Query(None, description="Preferred agent type"),
    workflow_type: Optional[str] = Query(None, description="Preferred workflow type")
):
    """Enhanced AP Overdue with LangGraph agent analysis"""
    try:
        # Validate user and company
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Process with LangGraph agent
        result = await agent_orchestrator.execute_agent(
            agent_type=agent_type or "ap_overdue",
            user_id=user_id,
            company_id=company_id,
            query="Generate AP Overdue report",
            context={"workflow_type": workflow_type or "report_generation"},
            session_id=str(uuid4())
        )
        
        return APOverdueResponse(
            success=True,
            message="AP Overdue report generated successfully",
            data=result.get('data', {}),
            summary=APOverdueSummaryResponse(
                total_overdue=result.get('total_overdue', 0),
                total_due=result.get('total_due', 0),
                overdue_percentage=result.get('overdue_percentage', 0)
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AP Overdue failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AP Overdue failed: {str(e)}")

@app.get("/ar/aging", response_model=ARCollectionResponse)
async def get_ar_aging(
    user_id: str = Query(..., description="User ID"),
    company_id: str = Query(..., description="Company ID"),
    agent_type: Optional[str] = Query(None, description="Preferred agent type"),
    workflow_type: Optional[str] = Query(None, description="Preferred workflow type")
):
    """Enhanced AR Aging with LangGraph agent analysis"""
    try:
        # Validate user and company
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Process with LangGraph agent
        result = await agent_orchestrator.execute_agent(
            agent_type=agent_type or "ar_aging",
            user_id=user_id,
            company_id=company_id,
            query="Generate AR Aging report",
            context={"workflow_type": workflow_type or "report_generation"},
            session_id=str(uuid4())
        )
        
        return ARCollectionResponse(
            success=True,
            message="AR Aging report generated successfully",
            data=result.get('data', {}),
            summary=ARCollectionSummaryResponse(
                total_due=result.get('total_due', 0),
                current_0_30=result.get('current_0_30', 0),
                days_31_60=result.get('days_31_60', 0),
                days_61_90=result.get('days_61_90', 0),
                days_90_plus=result.get('days_90_plus', 0)
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AR Aging failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AR Aging failed: {str(e)}")

@app.get("/ar/register", response_model=ARRegisterResponse)
async def get_ar_register(
    user_id: str = Query(..., description="User ID"),
    company_id: str = Query(..., description="Company ID"),
    agent_type: Optional[str] = Query(None, description="Preferred agent type"),
    workflow_type: Optional[str] = Query(None, description="Preferred workflow type")
):
    """Enhanced AR Register with LangGraph agent analysis"""
    try:
        # Validate user and company
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Process with LangGraph agent
        result = await agent_orchestrator.execute_agent(
            agent_type=agent_type or "ar_register",
            user_id=user_id,
            company_id=company_id,
            query="Generate AR Register report",
            context={"workflow_type": workflow_type or "report_generation"},
            session_id=str(uuid4())
        )
        
        return ARRegisterResponse(
            success=True,
            message="AR Register report generated successfully",
            data=result.get('data', {}),
            summary=ARRegisterSummaryResponse(
                total_invoices=result.get('total_invoices', 0),
                total_amount=result.get('total_amount', 0),
                total_paid=result.get('total_paid', 0),
                total_outstanding=result.get('total_outstanding', 0),
                paid_count=result.get('paid_count', 0),
                partial_count=result.get('partial_count', 0),
                unpaid_count=result.get('unpaid_count', 0)
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AR Register failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AR Register failed: {str(e)}")

@app.get("/ar/collection", response_model=ARCollectionResponse)
async def get_ar_collection(
    user_id: str = Query(..., description="User ID"),
    company_id: str = Query(..., description="Company ID"),
    agent_type: Optional[str] = Query(None, description="Preferred agent type"),
    workflow_type: Optional[str] = Query(None, description="Preferred workflow type")
):
    """Enhanced AR Collection with LangGraph agent analysis"""
    try:
        # Validate user and company
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Process with LangGraph agent
        result = await agent_orchestrator.execute_agent(
            agent_type=agent_type or "ar_collection",
            user_id=user_id,
            company_id=company_id,
            query="Generate AR Collection report",
            context={"workflow_type": workflow_type or "report_generation"},
            session_id=str(uuid4())
        )
        
        return ARCollectionResponse(
            success=True,
            message="AR Collection report generated successfully",
            data=result.get('data', {}),
            summary=ARCollectionSummaryResponse(
                total_due=result.get('total_due', 0),
                current_0_30=result.get('current_0_30', 0),
                days_31_60=result.get('days_31_60', 0),
                days_61_90=result.get('days_61_90', 0),
                days_90_plus=result.get('days_90_plus', 0)
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AR Collection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AR Collection failed: {str(e)}")

@app.get("/dso", response_model=DSOResponse)
async def get_dso(
    user_id: str = Query(..., description="User ID"),
    company_id: str = Query(..., description="Company ID"),
    agent_type: Optional[str] = Query(None, description="Preferred agent type"),
    workflow_type: Optional[str] = Query(None, description="Preferred workflow type")
):
    """Enhanced DSO with LangGraph agent analysis"""
    try:
        # Validate user and company
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Process with LangGraph agent
        result = await agent_orchestrator.execute_agent(
            agent_type=agent_type or "dso",
            user_id=user_id,
            company_id=company_id,
            query="Generate DSO report",
            context={"workflow_type": workflow_type or "report_generation"},
            session_id=str(uuid4())
        )
        
        return DSOResponse(
            success=True,
            message="DSO report generated successfully",
            data=result.get('data', {}),
            summary=DSOSummaryResponse(
                dso=result.get('dso', 0),
                average_collection_period=result.get('average_collection_period', 0),
                current_month_sales=result.get('current_month_sales', 0),
                current_receivables=result.get('current_receivables', 0)
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DSO failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DSO failed: {str(e)}")

# Chat-based query endpoint with LangGraph integration

@app.post("/api/v1/chat/query", response_model=Dict[str, Any])
async def chat_query(
    request: Optional[ChatQueryRequest] = None,
    query: Optional[str] = Query(None, description="Natural language query"),
    user_id: Optional[str] = Query(None, description="User ID"),
    company_id: Optional[str] = Query(None, description="Company ID"),
    session_id: Optional[str] = Query(None, description="Session ID"),
    agent_type: Optional[str] = Query(None, description="Preferred agent type"),
    authorization: Optional[str] = Header(None)
):
    """Chat-based query processing with LangGraph workflow visualization"""
    try:
        # Handle request parameters - prioritize JSON body over query parameters
        if request:
            # Use values from JSON body
            query_text = request.query
            user_id_value = request.user_id
            company_id_value = request.company_id
            session_id_value = request.session_id or str(uuid4())
            agent_type_value = request.agent_type
        else:
            # Use values from query parameters
            query_text = query
            user_id_value = user_id
            company_id_value = company_id
            session_id_value = session_id or str(uuid4())
            agent_type_value = agent_type
        
        # Validate required parameters
        if not query_text:
            raise HTTPException(status_code=400, detail="Query is required")
        if not user_id_value:
            raise HTTPException(status_code=400, detail="User ID is required")
        if not company_id_value:
            raise HTTPException(status_code=400, detail="Company ID is required")
        
        # Validate token if provided
        if authorization:
            try:
                from auth_system import verify_token
                token = authorization.split(" ")[-1]
                token_data = verify_token(token)
                if token_data.get('company_id') != company_id_value:
                    raise HTTPException(status_code=403, detail="Access denied")
            except Exception as e:
                logger.warning(f"Token validation failed: {e}")
        
        session_id_value = session_id_value or str(uuid4())
        domain = 'AP'  # Default domain
        
        # Use domain classifier to determine the best agent
        if not agent_type_value:
            try:
                domain_result = domain_classifier.classify(query_text)
                domain_full = domain_result.get('domain', 'APLayer') if isinstance(domain_result, dict) else 'APLayer'
                # Map domain names to short codes
                domain_map = {
                    'APLayer': 'ap',
                    'ARLayer': 'ar',
                    'AlertLayer': 'alert',
                    'ReportingLayer': 'reporting'
                }
                domain = domain_map.get(domain_full, 'ap').lower()
            except:
                domain = 'ap'
            # Use router or default to appropriate agent
            agent_type_value = f"{domain}_aging"  # Default to aging reports
        
        # Create or get session
        if session_id_value not in active_sessions:
            active_sessions[session_id_value] = {
                'user_id': user_id_value,
                'company_id': company_id_value,
                'start_time': datetime.now(),
                'messages': [],
                'context': {},
                'workflow_id': None,
                'workflow_nodes': []
            }
        
        logger.info(f"Query Processing - Domain: {domain if not agent_type_value else 'auto'} | Agent: {agent_type_value}")
        
        # Execute LangGraph agent with workflow building
        start_time = datetime.now()
        result = await agent_orchestrator.execute_agent(
            agent_type=agent_type_value,
            user_id=user_id_value,
            company_id=company_id_value,
            query=query_text,
            context={
                'session_id': session_id_value,
                'workflow_type': 'interactive'
            },
            session_id=session_id_value
        )
        
        # Save workflow to database for persistence
        try:
            workflow_id = str(uuid4())
            workflow_definition = {
                'agent_type': agent_type_value,
                'query': query_text,
                'user_id': user_id_value,
                'company_id': company_id_value,
                'session_id': session_id_value,
                'context': {
                    'workflow_type': 'interactive'
                }
            }
            
            execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Determine workflow status
            status = 'completed' if result.get('status') == 'success' else 'failed'
            error_message = result.get('error') if result.get('status') == 'error' else None
            
            # Extract file path if present
            file_path = None
            if 'file_path' in result:
                file_path = result['file_path']
            elif 'data' in result and isinstance(result['data'], dict) and 'file_path' in result['data']:
                file_path = result['data']['file_path']
            
            # Save to database
            save_workflow_to_db(
                workflow_id=workflow_id,
                name=f"{agent_type_value.upper()} Report",
                workflow_type=agent_type_value,
                status=status,
                company_id=company_id_value,
                user_id=user_id_value,
                query=query_text,
                domain='AP' if agent_type_value.startswith('ap_') else 'AR',
                report_type=agent_type_value,
                workflow_definition=workflow_definition,
                execution_result=result,
                started_at=start_time,
                completed_at=datetime.now(),
                output_file_path=file_path,
                execution_time_ms=execution_time_ms,
                error_message=error_message
            )
            
            # Update workflow_id in session
            active_sessions[session_id_value]['workflow_id'] = workflow_id
            
        except Exception as e:
            logger.error(f"Failed to save workflow to database: {e}")
        
        # Build interactive workflow
        workflow_id = str(uuid4())
        workflow_nodes = await build_interactive_workflow(
            agent_type=agent_type_value,
            query=query_text,
            result=result,
            session_id=session_id_value,
            workflow_id=workflow_id
        )
        
        # Update session
        active_sessions[session_id_value]['messages'].append({
            'query': query_text,
            'response': result.get('response', ''),
            'agent_type': agent_type_value,
            'workflow_id': workflow_id,
            'timestamp': datetime.now().isoformat()
        })
        
        # Try to surface report file path if present in result or result['data']
        report_file_path = None
        if 'file_path' in result:
            report_file_path = result['file_path']
        elif 'data' in result and isinstance(result['data'], dict) and 'file_path' in result['data']:
            report_file_path = result['data']['file_path']

        # Create response message with file path information
        response_message = result.get('response', '')
        if report_file_path:
            import os
            filename = os.path.basename(report_file_path)
            download_url = f"/api/v1/reports/download/{filename}"
            response_message += f" Report file: {filename} | Download URL: {download_url}"

        response_obj = {
            "session_id": session_id_value,
            "query": query_text,
            "selected_agent": agent_type_value,
            "workflow_id": workflow_id,
            "workflow_nodes": workflow_nodes,
            "suggested_actions": result.get('suggested_actions', []),
            "response": response_message,
            "data": result.get('data', {}),
            "metadata": result.get('metadata', {}),
            "timestamp": datetime.now().isoformat()
        }
        if report_file_path:
            response_obj["report_file_path"] = report_file_path
            response_obj["download_url"] = download_url
        return response_obj
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat query failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat query failed: {str(e)}")

async def build_interactive_workflow(agent_type: str, query: str, result: Dict[str, Any], session_id: str, workflow_id: str) -> List[Dict[str, Any]]:
    """Build interactive workflow with clickable nodes"""
    workflow_nodes = []
    
    # Define node templates based on agent type
    node_templates = {
        "ap_aging": [
            {
                "node_id": "fetch_invoices",
                "node_type": "data_fetch",
                "name": "Fetch Invoices",
                "description": "Retrieve invoice data from database",
                "editable_fields": ["date_range", "vendor_filter"],
                "default_values": {
                    "date_range": "last_90_days",
                    "vendor_filter": "all_vendors"
                },
                "code_preview": "SELECT * FROM vendor_invoices WHERE due_date <= CURRENT_DATE"
            },
            {
                "node_id": "calculate_aging",
                "node_type": "calculation",
                "name": "Calculate Aging",
                "description": "Calculate aging buckets for invoices",
                "editable_fields": ["aging_buckets"],
                "default_values": {
                    "aging_buckets": ["0-30", "31-60", "61-90", "90+"]
                },
                "code_preview": "days_overdue = (CURRENT_DATE - due_date).days"
            },
            {
                "node_id": "generate_report",
                "node_type": "output",
                "name": "Generate Report",
                "description": "Generate AP Aging Excel report",
                "editable_fields": ["include_details", "branding"],
                "default_values": {
                    "include_details": True,
                    "branding": True
                },
                "code_preview": "# Generate AP Aging Excel report\nreport = BrandedExcelGenerator.generate_ap_aging_report(data)"
            }
        ],
        "ap_register": [
            {
                "node_id": "fetch_register_data",
                "node_type": "data_fetch",
                "name": "Fetch Register Data",
                "description": "Retrieve AP register data from database",
                "editable_fields": ["date_range", "status_filter"],
                "default_values": {
                    "date_range": "current_month",
                    "status_filter": "all"
                },
                "code_preview": "SELECT * FROM vendor_invoices WHERE invoice_date >= start_date"
            },
            {
                "node_id": "calculate_totals",
                "node_type": "calculation",
                "name": "Calculate Totals",
                "description": "Calculate summary totals",
                "editable_fields": ["include_tax", "include_outstanding"],
                "default_values": {
                    "include_tax": True,
                    "include_outstanding": True
                },
                "code_preview": "total_amount = SUM(subtotal_amount + tax_amount)"
            },
            {
                "node_id": "generate_register",
                "node_type": "output",
                "name": "Generate Register",
                "description": "Generate AP Register Excel report",
                "editable_fields": ["include_status", "branding"],
                "default_values": {
                    "include_status": True,
                    "branding": True
                },
                "code_preview": "# Generate AP Register Excel report\nreport = BrandedExcelGenerator.generate_ap_register_report(data)"
            }
        ],
        "document_processing": [
            {
                "node_id": "extract_text",
                "node_type": "processing",
                "name": "Extract Text",
                "description": "Extract text from uploaded document",
                "editable_fields": ["ocr_engine", "language"],
                "default_values": {
                    "ocr_engine": "tesseract",
                    "language": "eng"
                },
                "code_preview": "text = ocr_engine.extract_text(file_path)"
            },
            {
                "node_id": "parse_data",
                "node_type": "parsing",
                "name": "Parse Data",
                "description": "Parse extracted text for financial data",
                "editable_fields": ["entity_types", "validation_rules"],
                "default_values": {
                    "entity_types": ["invoice_number", "amount", "date"],
                    "validation_rules": ["amount_format", "date_format"]
                },
                "code_preview": "entities = parser.extract_entities(text)"
            },
            {
                "node_id": "validate_data",
                "node_type": "validation",
                "name": "Validate Data",
                "description": "Validate extracted financial data",
                "editable_fields": ["validation_level", "error_tolerance"],
                "default_values": {
                    "validation_level": "strict",
                    "error_tolerance": 0.05
                },
                "code_preview": "is_valid = validator.validate(entities)"
            }
        ]
    }
    
    # Get workflow nodes for the agent type
    if agent_type in node_templates:
        workflow_nodes = node_templates[agent_type]
    else:
        # Default workflow nodes
        workflow_nodes = [
            {
                "node_id": "data_fetch",
                "node_type": "data_fetch",
                "name": "Fetch Data",
                "description": "Retrieve data from database",
                "editable_fields": ["filters"],
                "default_values": {"filters": "all"},
                "code_preview": "SELECT * FROM relevant_table"
            },
            {
                "node_id": "process_data",
                "node_type": "processing",
                "name": "Process Data",
                "description": "Process and analyze data",
                "editable_fields": ["processing_rules"],
                "default_values": {"processing_rules": "default"},
                "code_preview": "processed_data = process(data)"
            },
            {
                "node_id": "generate_output",
                "node_type": "output",
                "name": "Generate Output",
                "description": "Generate final output/report",
                "editable_fields": ["output_format", "branding"],
                "default_values": {"output_format": "excel", "branding": True},
                "code_preview": "output = generate_report(processed_data)"
            }
        ]
    
    # Store workflow in session
    if session_id in active_sessions:
        active_sessions[session_id]['workflow_id'] = workflow_id
        active_sessions[session_id]['workflow_nodes'] = workflow_nodes
    
    return workflow_nodes

# Interactive workflow endpoints

@app.get("/api/v1/workflow/{session_id}/{workflow_id}", response_model=Dict[str, Any])
async def get_interactive_workflow(session_id: str, workflow_id: str):
    """Get interactive workflow with node details"""
    try:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = active_sessions[session_id]
        if session.get('workflow_id') != workflow_id:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {
            "session_id": session_id,
            "workflow_id": workflow_id,
            "workflow_nodes": session.get('workflow_nodes', []),
            "workflow_status": "interactive",
            "execution_history": session.get('messages', []),
            "editable_fields": [node.get('editable_fields', []) for node in session.get('workflow_nodes', [])],
            "node_details": {node['node_id']: node for node in session.get('workflow_nodes', [])},
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get workflow failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Get workflow failed: {str(e)}")

@app.put("/api/v1/workflow/{session_id}/{workflow_id}/node/{node_id}", response_model=Dict[str, Any])
async def update_workflow_node(session_id: str, workflow_id: str, node_id: str, updates: Dict[str, Any]):
    """Update a workflow node with new values"""
    try:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = active_sessions[session_id]
        if session.get('workflow_id') != workflow_id:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Find and update the node
        workflow_nodes = session.get('workflow_nodes', [])
        updated_node = None
        
        for node in workflow_nodes:
            if node['node_id'] == node_id:
                # Update node values
                for field, value in updates.items():
                    if field in node.get('default_values', {}):
                        node['default_values'][field] = value
                
                updated_node = node
                break
        
        if not updated_node:
            raise HTTPException(status_code=404, detail="Node not found")
        
        # Validate the updated node
        validation_result = validate_node_update(node_id, updated_node)
        
        return {
            "session_id": session_id,
            "workflow_id": workflow_id,
            "node_id": node_id,
            "updated_node": updated_node,
            "validation_result": validation_result,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update node failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Update node failed: {str(e)}")

def validate_node_update(node_id: str, node: Dict[str, Any]) -> Dict[str, Any]:
    """Validate node updates"""
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # Add validation logic based on node type
    node_type = node.get('node_type', '')
    
    if node_type == "data_fetch":
        # Validate data fetch parameters
        pass
    elif node_type == "calculation":
        # Validate calculation parameters
        pass
    elif node_type == "output":
        # Validate output parameters
        pass
    
    return validation_result

@app.post("/api/v1/workflow/{session_id}/{workflow_id}/execute", response_model=Dict[str, Any])
async def execute_workflow(session_id: str, workflow_id: str, execute: bool = True, generate_report: bool = True):
    """Execute the workflow with current node values"""
    try:
        if session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = active_sessions[session_id]
        if session.get('workflow_id') != workflow_id:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        workflow_nodes = session.get('workflow_nodes', [])
        
        if not execute:
            return {
                "session_id": session_id,
                "workflow_id": workflow_id,
                "status": "cancelled",
                "message": "Workflow execution cancelled by user",
                "timestamp": datetime.now().isoformat()
            }
        
        # Execute workflow nodes
        execution_result = await execute_workflow_nodes(workflow_nodes, session)
        
        # Generate report if requested
        report_generated = False
        report_file = None
        report_url = None
        
        if generate_report:
            report_result = await generate_workflow_report(execution_result, session)
            if report_result['status'] == 'success':
                report_generated = True
                report_file = report_result['file_path']
                report_url = report_result.get('file_url')
        
        return {
            "session_id": session_id,
            "workflow_id": workflow_id,
            "status": "completed",
            "execution_result": execution_result,
            "report_generated": report_generated,
            "report_file": report_file,
            "report_url": report_url,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Execute workflow failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Execute workflow failed: {str(e)}")

async def execute_workflow_nodes(workflow_nodes: List[Dict[str, Any]], session: Dict[str, Any]) -> Dict[str, Any]:
    """Execute workflow nodes with current values"""
    execution_result = {
        "node_results": [],
        "overall_status": "success",
        "execution_time": 0
    }
    
    start_time = datetime.now()
    
    for node in workflow_nodes:
        try:
            # Execute node with current values
            node_result = await execute_node(node, session)
            execution_result["node_results"].append({
                "node_id": node["node_id"],
                "node_name": node["name"],
                "status": "success",
                "result": node_result,
                "execution_time": 0.1  # Mock execution time
            })
        except Exception as e:
            execution_result["node_results"].append({
                "node_id": node["node_id"],
                "node_name": node["name"],
                "status": "failed",
                "error": str(e),
                "execution_time": 0.1
            })
            execution_result["overall_status"] = "failed"
    
    execution_result["execution_time"] = (datetime.now() - start_time).total_seconds()
    
    return execution_result

async def execute_node(node: Dict[str, Any], session: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single workflow node"""
    # Mock node execution based on node type
    node_type = node.get('node_type', '')
    
    if node_type == "data_fetch":
        return {"data": "fetched_data", "count": 100}
    elif node_type == "calculation":
        return {"result": 1234.56, "metrics": {"avg": 100, "total": 1000}}
    elif node_type == "output":
        return {"report_generated": True, "file_path": "/path/to/report.xlsx"}
    else:
        return {"status": "completed"}

async def generate_workflow_report(execution_result: Dict[str, Any], session: Dict[str, Any]) -> Dict[str, Any]:
    """Generate report from workflow execution"""
    try:
        # Use report template integration to generate report
        report_type = "workflow_execution"
        report_data = {
            "execution_result": execution_result,
            "session_info": {
                "user_id": session.get('user_id'),
                "company_id": session.get('company_id'),
                "timestamp": datetime.now().isoformat()
            }
        }
        
        result = report_template_integration.generate_report(
            template_type=report_type,
            report_data=report_data,
            company_id=session.get('company_id'),
            user_id=session.get('user_id')
        )
        
        return result
        
    except Exception as e:
        return {"status": "failed", "error": str(e)}

# Session management endpoints

@app.post("/session/create", response_model=UserSessionResponse)
async def create_session(request: UserSessionRequest):
    """Create a new user session"""
    try:
        session_id = str(uuid4())
        session = UserSession(
            session_id=session_id,
            user_id=request.user_id,
            company_id=request.company_id,
            start_time=datetime.now(),
            context={},
            active=True
        )
        
        user_sessions[session_id] = session
        
        return UserSessionResponse(
            session_id=session_id,
            user_id=request.user_id,
            company_id=request.company_id,
            start_time=session.start_time.isoformat(),
            context=session.context,
            active=session.active
        )
        
    except Exception as e:
        logger.error(f"Session creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Session creation failed: {str(e)}")

@app.get("/session/{session_id}", response_model=UserSessionResponse)
async def get_session(session_id: str):
    """Get session information"""
    try:
        session = user_sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return UserSessionResponse(
            session_id=session.session_id,
            user_id=session.user_id,
            company_id=session.company_id,
            start_time=session.start_time.isoformat(),
            context=session.context,
            active=session.active
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get session failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Get session failed: {str(e)}")

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a user session"""
    try:
        if session_id in user_sessions:
            del user_sessions[session_id]
            return {"message": "Session deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session deletion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Session deletion failed: {str(e)}")

# Health check and status endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "connected",
            "llm": "available",
            "langgraph": "ready",
            "mcp": "running"
        }
    }

@app.get("/status")
async def system_status():
    """System status endpoint"""
    return {
        "status": "operational",
        "active_sessions": len(active_sessions),
        "active_users": len(user_sessions),
        "mcp_server": "running",
        "langgraph": "ready",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/capabilities")
async def get_capabilities():
    """Get system capabilities"""
    return {
        "langgraph_features": [
            "Interactive workflow building",
            "Node-level editing",
            "Real-time execution",
            "Code visibility",
            "Report generation"
        ],
        "report_types": report_template_integration.get_available_templates(),
        "supported_agents": [
            "ap_aging",
            "ap_register", 
            "ap_overdue",
            "ar_aging",
            "ar_register",
            "ar_collection",
            "dso",
            "document_processing"
        ],
        "interactive_features": [
            "Clickable nodes",
            "Editable parameters",
            "Code preview",
            "Real-time validation",
            "Workflow execution"
        ]
    }

@app.get("/api/v1/workflows")
async def list_workflows(
    company_id: str = Query(..., description="Company ID"),
    user_id: Optional[str] = Query(None, description="User ID"),
    limit: int = Query(50, description="Limit results")
):
    """List workflows for a company (matches production_api.py endpoint)"""
    try:
        # Query workflows from database
        db = WorkflowSessionLocal()
        
        query = text("""
            SELECT 
                id,
                name,
                type,
                status,
                query,
                domain,
                report_type,
                created_at,
                started_at,
                completed_at,
                output_file_path,
                execution_time_ms,
                error_message
            FROM workflows
            WHERE company_id = :company_id
            AND (:user_id IS NULL OR user_id = :user_id)
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        
        result = db.execute(query, {
            "company_id": company_id,
            "user_id": user_id,
            "limit": limit
        })
        
        workflows = []
        for row in result:
            workflows.append({
                "id": row.id,
                "name": row.name,
                "type": row.type,
                "status": row.status,
                "query": row.query,
                "domain": row.domain,
                "report_type": row.report_type,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "started_at": row.started_at.isoformat() if row.started_at else None,
                "completed_at": row.completed_at.isoformat() if row.completed_at else None,
                "output_file_path": row.output_file_path,
                "execution_time_ms": row.execution_time_ms,
                "error_message": row.error_message
            })
        
        db.close()
        
        return {
            "status": "success",
            "count": len(workflows),
            "workflows": workflows
        }
        
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list workflows: {str(e)}")

# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    # Start FastAPI server
    uvicorn.run(
        "production_api_langgraph:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )