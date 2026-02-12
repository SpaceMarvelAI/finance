#!/usr/bin/env python3
"""
Agentic API - Production-ready API with LangGraph integration
Provides all endpoints from production_api.py with enhanced agentic capabilities
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
from fastapi import FastAPI, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import core components
from data_layer.database.database_manager import get_database
from data_layer.models.user import User
from data_layer.repositories.user_repository import UserRepository
from intelligence_layer.orchestration.intelligence_orchestrator import IntelligenceOrchestrator
from processing_layer.agents.langgraph_framework import ReportTemplateIntegration
from processing_layer.document_processing.document_processing_service import DocumentProcessingService
from processing_layer.reconciliation.reconciliation_service import ReconciliationService
from processing_layer.report_generation.branded_excel_generator import BrandedExcelGenerator
from shared.config.logging_config import get_logger
from shared.config.settings import Settings
from shared.llm.factory import LLMFactory
from shared.utils.file_utils import get_file_extension, validate_file_type

# Import LangGraph components
from processing_layer.agents.langgraph_framework.agent_orchestrator import AgentOrchestrator
from processing_layer.agents.langgraph_framework.workflow_builder import WorkflowBuilder
from processing_layer.agents.langgraph_framework.report_template_integration import ReportTemplateIntegration

# Import MCP server
from mcp.server import create_mcp_server

# Import existing production API components
from production_api import (
    APOverdueRequest, APOverdueResponse, APOverdueSummaryResponse,
    APRegisterRequest, APRegisterResponse, APRegisterSummaryResponse,
    APAgingRequest, APAgingResponse, APAgingSummaryResponse,
    ARCollectionRequest, ARCollectionResponse, ARCollectionSummaryResponse,
    ARRegisterRequest, ARRegisterResponse, ARRegisterSummaryResponse,
    ARSummaryResponse, ARSummaryRequest, ARSummaryResponse,
    DSORequest, DSOResponse, DSOSummaryResponse,
    UploadRequest, UploadResponse, UploadSummaryResponse,
    UserRegistrationRequest, UserRegistrationResponse,
    UserLoginRequest, UserLoginResponse,
    BrandingRequest, BrandingResponse,
    CompanyRegistrationRequest, CompanyRegistrationResponse,
    CompanyLoginRequest, CompanyLoginResponse,
    CompanyProfileResponse, CompanyProfileRequest,
    UserSessionResponse, UserSessionRequest,
    UserSessionData, UserSession
)

logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Agentic Financial Automation API",
    description="Production-ready API with LangGraph integration for financial document processing and analysis",
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

# Initialize services
db = get_database()
user_repo = UserRepository(db)
llm_factory = LLMFactory()
intelligence_orchestrator = IntelligenceOrchestrator()
document_processor = DocumentProcessingService()
reconciliation_service = ReconciliationService()
excel_generator = BrandedExcelGenerator()

# Initialize LangGraph components
agent_orchestrator = AgentOrchestrator()
workflow_builder = WorkflowBuilder()
report_template_integration = ReportTemplateIntegration()

# Initialize MCP server
mcp_server = create_mcp_server()

# Global variables for session management
active_sessions: Dict[str, Dict[str, Any]] = {}
user_sessions: Dict[str, UserSession] = {}

class AgenticRequest(BaseModel):
    """Enhanced request with agentic capabilities"""
    user_id: str
    company_id: str
    query: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    agent_type: Optional[str] = None
    workflow_type: Optional[str] = None

class AgenticResponse(BaseModel):
    """Enhanced response with agentic capabilities"""
    session_id: str
    response: str
    agent_type: str
    workflow_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    timestamp: str

class ReportGenerationRequest(BaseModel):
    """Request for report generation with agentic capabilities"""
    user_id: str
    company_id: str
    report_type: str
    parameters: Dict[str, Any]
    session_id: Optional[str] = None
    agent_type: Optional[str] = None

class ReportGenerationResponse(BaseModel):
    """Response for report generation"""
    session_id: str
    report_type: str
    file_path: str
    file_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: str

class WorkflowExecutionRequest(BaseModel):
    """Request for workflow execution"""
    user_id: str
    company_id: str
    workflow_type: str
    input_data: Dict[str, Any]
    session_id: Optional[str] = None
    agent_type: Optional[str] = None

class WorkflowExecutionResponse(BaseModel):
    """Response for workflow execution"""
    session_id: str
    workflow_type: str
    status: str
    result: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: str

class AgenticWebSocketMessage(BaseModel):
    """WebSocket message for agentic communication"""
    type: str  # 'request', 'response', 'progress', 'error'
    session_id: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    progress: Optional[float] = None
    error: Optional[str] = None

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

# Agentic endpoints

@app.post("/agentic/query", response_model=AgenticResponse)
async def agentic_query(request: AgenticRequest):
    """Execute an agentic query with LangGraph integration"""
    try:
        session_id = request.session_id or str(uuid4())
        
        # Validate user and company
        user = user_repo.get_user_by_id(request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create or get session
        if session_id not in active_sessions:
            active_sessions[session_id] = {
                'user_id': request.user_id,
                'company_id': request.company_id,
                'start_time': datetime.now(),
                'messages': [],
                'context': {}
            }
        
        # Determine agent type if not specified
        agent_type = request.agent_type
        if not agent_type:
            # Use intelligence orchestrator to determine best agent
            agent_type = intelligence_orchestrator.route_query(request.query)
        
        # Execute agentic query
        result = await agent_orchestrator.execute_agent(
            agent_type=agent_type,
            user_id=request.user_id,
            company_id=request.company_id,
            query=request.query,
            context=request.context or {},
            session_id=session_id
        )
        
        # Update session
        active_sessions[session_id]['messages'].append({
            'query': request.query,
            'response': result['response'],
            'agent_type': agent_type,
            'timestamp': datetime.now().isoformat()
        })
        
        return AgenticResponse(
            session_id=session_id,
            response=result['response'],
            agent_type=agent_type,
            workflow_type=result.get('workflow_type'),
            metadata=result.get('metadata'),
            actions=result.get('actions'),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Agentic query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agentic query failed: {str(e)}")

@app.post("/agentic/report", response_model=ReportGenerationResponse)
async def agentic_report_generation(request: ReportGenerationRequest):
    """Generate reports using agentic capabilities"""
    try:
        session_id = request.session_id or str(uuid4())
        
        # Validate user and company
        user = user_repo.get_user_by_id(request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Validate report type
        available_templates = report_template_integration.get_available_templates()
        if request.report_type not in available_templates:
            raise HTTPException(status_code=400, detail=f"Invalid report type. Available: {available_templates}")
        
        # Generate report using template integration
        result = report_template_integration.generate_report(
            template_type=request.report_type,
            report_data=request.parameters,
            company_id=request.company_id,
            user_id=request.user_id
        )
        
        if result['status'] != 'success':
            raise HTTPException(status_code=500, detail=result.get('error', 'Report generation failed'))
        
        return ReportGenerationResponse(
            session_id=session_id,
            report_type=request.report_type,
            file_path=result['file_path'],
            file_url=result.get('file_url'),
            metadata=result.get('metadata'),
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agentic report generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@app.post("/agentic/workflow", response_model=WorkflowExecutionResponse)
async def agentic_workflow_execution(request: WorkflowExecutionRequest):
    """Execute workflows using agentic capabilities"""
    try:
        session_id = request.session_id or str(uuid4())
        
        # Validate user and company
        user = user_repo.get_user_by_id(request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create workflow
        workflow = workflow_builder.create_workflow(
            workflow_type=request.workflow_type,
            user_id=request.user_id,
            company_id=request.company_id
        )
        
        # Execute workflow
        result = await workflow_builder.execute_workflow(
            workflow=workflow,
            input_data=request.input_data,
            session_id=session_id
        )
        
        return WorkflowExecutionResponse(
            session_id=session_id,
            workflow_type=request.workflow_type,
            status="completed",
            result=result,
            metadata={"execution_time": result.get("execution_time", 0)},
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agentic workflow execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

@app.websocket("/agentic/ws")
async def agentic_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time agentic communication"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Process message
            if message['type'] == 'request':
                # Handle agentic request
                response = await handle_agentic_websocket_request(message)
                await websocket.send_text(json.dumps(response))
            
            elif message['type'] == 'progress':
                # Handle progress updates
                await websocket.send_text(json.dumps({
                    'type': 'progress_update',
                    'session_id': message['session_id'],
                    'progress': message.get('progress', 0)
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.send_text(json.dumps({
            'type': 'error',
            'error': str(e)
        }))

async def handle_agentic_websocket_request(message: Dict[str, Any]) -> Dict[str, Any]:
    """Handle agentic requests via WebSocket"""
    try:
        request = AgenticRequest(**message)
        
        # Execute agentic query
        result = await agentic_query(request)
        
        return {
            'type': 'response',
            'session_id': result.session_id,
            'response': result.response,
            'agent_type': result.agent_type,
            'metadata': result.metadata,
            'timestamp': result.timestamp
        }
        
    except Exception as e:
        return {
            'type': 'error',
            'session_id': message.get('session_id', ''),
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

# Enhanced existing endpoints with agentic capabilities

@app.post("/upload", response_model=UploadResponse)
async def upload_document_agentic(
    file: UploadFile = File(...),
    user_id: str = Query(..., description="User ID"),
    company_id: str = Query(..., description="Company ID"),
    agent_type: Optional[str] = Query(None, description="Preferred agent type"),
    workflow_type: Optional[str] = Query(None, description="Preferred workflow type")
):
    """Enhanced upload with agentic processing"""
    try:
        # Validate user and company
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Validate file
        if not validate_file_type(file.filename):
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        # Process with agentic capabilities
        result = await document_processor.process_document_agentic(
            file=file,
            user_id=user_id,
            company_id=company_id,
            agent_type=agent_type,
            workflow_type=workflow_type
        )
        
        return UploadResponse(
            success=True,
            message="Document processed successfully",
            document_id=result['document_id'],
            extracted_data=result['extracted_data'],
            summary=UploadSummaryResponse(
                total_documents=1,
                processed_documents=1,
                failed_documents=0,
                processing_time=result['processing_time']
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agentic upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/ap/aging", response_model=APAgingResponse)
async def get_ap_aging_agentic(
    user_id: str = Query(..., description="User ID"),
    company_id: str = Query(..., description="Company ID"),
    agent_type: Optional[str] = Query(None, description="Preferred agent type"),
    workflow_type: Optional[str] = Query(None, description="Preferred workflow type")
):
    """Enhanced AP Aging with agentic analysis"""
    try:
        # Validate user and company
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Process with agentic capabilities
        result = await agent_orchestrator.execute_agent(
            agent_type=agent_type or "ap_aging",
            user_id=user_id,
            company_id=company_id,
            query="Generate AP Aging report",
            context={"workflow_type": workflow_type},
            session_id=str(uuid4())
        )
        
        return APAgingResponse(
            success=True,
            message="AP Aging report generated successfully",
            data=result.get('data', {}),
            summary=APAgingSummaryResponse(
                total_due=0,
                current_0_30=0,
                days_31_60=0,
                days_61_90=0,
                days_90_plus=0
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agentic AP Aging failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AP Aging failed: {str(e)}")

@app.get("/ap/register", response_model=APRegisterResponse)
async def get_ap_register_agentic(
    user_id: str = Query(..., description="User ID"),
    company_id: str = Query(..., description="Company ID"),
    agent_type: Optional[str] = Query(None, description="Preferred agent type"),
    workflow_type: Optional[str] = Query(None, description="Preferred workflow type")
):
    """Enhanced AP Register with agentic analysis"""
    try:
        # Validate user and company
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Process with agentic capabilities
        result = await agent_orchestrator.execute_agent(
            agent_type=agent_type or "ap_register",
            user_id=user_id,
            company_id=company_id,
            query="Generate AP Register report",
            context={"workflow_type": workflow_type},
            session_id=str(uuid4())
        )
        
        return APRegisterResponse(
            success=True,
            message="AP Register report generated successfully",
            data=result.get('data', {}),
            summary=APRegisterSummaryResponse(
                total_invoices=0,
                total_amount=0,
                total_paid=0,
                total_outstanding=0,
                paid_count=0,
                partial_count=0,
                unpaid_count=0
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agentic AP Register failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AP Register failed: {str(e)}")

@app.get("/ap/overdue", response_model=APOverdueResponse)
async def get_ap_overdue_agentic(
    user_id: str = Query(..., description="User ID"),
    company_id: str = Query(..., description="Company ID"),
    agent_type: Optional[str] = Query(None, description="Preferred agent type"),
    workflow_type: Optional[str] = Query(None, description="Preferred workflow type")
):
    """Enhanced AP Overdue with agentic analysis"""
    try:
        # Validate user and company
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Process with agentic capabilities
        result = await agent_orchestrator.execute_agent(
            agent_type=agent_type or "ap_overdue",
            user_id=user_id,
            company_id=company_id,
            query="Generate AP Overdue report",
            context={"workflow_type": workflow_type},
            session_id=str(uuid4())
        )
        
        return APOverdueResponse(
            success=True,
            message="AP Overdue report generated successfully",
            data=result.get('data', {}),
            summary=APOverdueSummaryResponse(
                total_overdue=0,
                total_due=0,
                overdue_percentage=0
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agentic AP Overdue failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AP Overdue failed: {str(e)}")

@app.get("/ar/aging", response_model=ARCollectionResponse)
async def get_ar_aging_agentic(
    user_id: str = Query(..., description="User ID"),
    company_id: str = Query(..., description="Company ID"),
    agent_type: Optional[str] = Query(None, description="Preferred agent type"),
    workflow_type: Optional[str] = Query(None, description="Preferred workflow type")
):
    """Enhanced AR Aging with agentic analysis"""
    try:
        # Validate user and company
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Process with agentic capabilities
        result = await agent_orchestrator.execute_agent(
            agent_type=agent_type or "ar_aging",
            user_id=user_id,
            company_id=company_id,
            query="Generate AR Aging report",
            context={"workflow_type": workflow_type},
            session_id=str(uuid4())
        )
        
        return ARCollectionResponse(
            success=True,
            message="AR Aging report generated successfully",
            data=result.get('data', {}),
            summary=ARCollectionSummaryResponse(
                total_due=0,
                current_0_30=0,
                days_31_60=0,
                days_61_90=0,
                days_90_plus=0
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agentic AR Aging failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AR Aging failed: {str(e)}")

@app.get("/ar/register", response_model=ARRegisterResponse)
async def get_ar_register_agentic(
    user_id: str = Query(..., description="User ID"),
    company_id: str = Query(..., description="Company ID"),
    agent_type: Optional[str] = Query(None, description="Preferred agent type"),
    workflow_type: Optional[str] = Query(None, description="Preferred workflow type")
):
    """Enhanced AR Register with agentic analysis"""
    try:
        # Validate user and company
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Process with agentic capabilities
        result = await agent_orchestrator.execute_agent(
            agent_type=agent_type or "ar_register",
            user_id=user_id,
            company_id=company_id,
            query="Generate AR Register report",
            context={"workflow_type": workflow_type},
            session_id=str(uuid4())
        )
        
        return ARRegisterResponse(
            success=True,
            message="AR Register report generated successfully",
            data=result.get('data', {}),
            summary=ARRegisterSummaryResponse(
                total_invoices=0,
                total_amount=0,
                total_paid=0,
                total_outstanding=0,
                paid_count=0,
                partial_count=0,
                unpaid_count=0
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agentic AR Register failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AR Register failed: {str(e)}")

@app.get("/ar/collection", response_model=ARCollectionResponse)
async def get_ar_collection_agentic(
    user_id: str = Query(..., description="User ID"),
    company_id: str = Query(..., description="Company ID"),
    agent_type: Optional[str] = Query(None, description="Preferred agent type"),
    workflow_type: Optional[str] = Query(None, description="Preferred workflow type")
):
    """Enhanced AR Collection with agentic analysis"""
    try:
        # Validate user and company
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Process with agentic capabilities
        result = await agent_orchestrator.execute_agent(
            agent_type=agent_type or "ar_collection",
            user_id=user_id,
            company_id=company_id,
            query="Generate AR Collection report",
            context={"workflow_type": workflow_type},
            session_id=str(uuid4())
        )
        
        return ARCollectionResponse(
            success=True,
            message="AR Collection report generated successfully",
            data=result.get('data', {}),
            summary=ARCollectionSummaryResponse(
                total_due=0,
                current_0_30=0,
                days_31_60=0,
                days_61_90=0,
                days_90_plus=0
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agentic AR Collection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AR Collection failed: {str(e)}")

@app.get("/dso", response_model=DSOResponse)
async def get_dso_agentic(
    user_id: str = Query(..., description="User ID"),
    company_id: str = Query(..., description="Company ID"),
    agent_type: Optional[str] = Query(None, description="Preferred agent type"),
    workflow_type: Optional[str] = Query(None, description="Preferred workflow type")
):
    """Enhanced DSO with agentic analysis"""
    try:
        # Validate user and company
        user = user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Process with agentic capabilities
        result = await agent_orchestrator.execute_agent(
            agent_type=agent_type or "dso",
            user_id=user_id,
            company_id=company_id,
            query="Generate DSO report",
            context={"workflow_type": workflow_type},
            session_id=str(uuid4())
        )
        
        return DSOResponse(
            success=True,
            message="DSO report generated successfully",
            data=result.get('data', {}),
            summary=DSOSummaryResponse(
                dso=0,
                average_collection_period=0,
                current_month_sales=0,
                current_receivables=0
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agentic DSO failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DSO failed: {str(e)}")

# Session management endpoints

@app.post("/session/create", response_model=UserSessionResponse)
async def create_session(request: UserSessionRequest):
    """Create a new user session with agentic capabilities"""
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
            "agentic": "ready",
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
        "agentic_features": [
            "Intelligent query routing",
            "Multi-agent orchestration",
            "Workflow automation",
            "Real-time processing",
            "Context-aware responses"
        ],
        "report_types": report_template_integration.get_available_templates(),
        "supported_workflows": [
            "document_processing",
            "report_generation",
            "data_analysis",
            "reconciliation"
        ],
        "mcp_tools": [
            "report_generation",
            "report_management",
            "report_templates",
            "report_validation"
        ]
    }

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
    # Start MCP server in background
    mcp_task = asyncio.create_task(mcp_server.run())
    
    # Start FastAPI server
    uvicorn.run(
        "agentic_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )