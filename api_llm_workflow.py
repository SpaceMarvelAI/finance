"""
API for LLM Workflow Generation
Demonstrates Phase 3.1: Foundation & Data Integration
"""

from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import asyncio
from datetime import datetime
import logging

# Import our LLM workflow components
from processing_layer.workflows.llm_workflow_generator import LLMWorkflowGenerator
from processing_layer.agents.langgraph_framework.llm_integration import LLMWorkflowIntegration
from shared.config.logging_config import get_logger


logger = get_logger(__name__)

app = FastAPI(
    title="LLM Workflow Generation API",
    description="Phase 3.1: Foundation & Data Integration",
    version="3.1.0"
)


class QueryRequest(BaseModel):
    query: str
    company_id: str
    user_id: str


class WorkflowResponse(BaseModel):
    workflow_id: str
    workflow_definition: Dict[str, Any]
    status: str
    message: str
    timestamp: str


class CustomNodeRequest(BaseModel):
    title: str
    node_type: str
    description: str
    params: Dict[str, Any] = {}


# Global instances
workflow_generator = LLMWorkflowGenerator()
llm_integration = LLMWorkflowIntegration()


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "LLM Workflow Generation API - Phase 3.1",
        "version": "3.1.0",
        "description": "Foundation & Data Integration for agent-driven workflow generation",
        "endpoints": {
            "POST /generate-workflow": "Generate workflow from natural language query",
            "POST /create-custom-node": "Create custom workflow node",
            "GET /health": "Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "llm_generator": "active",
            "llm_integration": "active",
            "database": "connected"
        }
    }


@app.post("/generate-workflow", response_model=WorkflowResponse)
async def generate_workflow(request: QueryRequest):
    """
    Generate workflow from natural language query
    
    Example queries:
    - "Generate AP aging report for last 90 days"
    - "Create AR register with outstanding amounts"
    - "Show overdue invoices grouped by vendor"
    """
    try:
        logger.info(f"Generating workflow for query: {request.query}")
        
        # Generate workflow using LLM
        workflow_definition = await llm_integration.generate_workflow_from_query(
            request.query, 
            request.company_id, 
            request.user_id
        )
        
        # Generate workflow ID
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        response = WorkflowResponse(
            workflow_id=workflow_id,
            workflow_definition=workflow_definition,
            status="success",
            message="Workflow generated successfully",
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"Successfully generated workflow: {workflow_id}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to generate workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/create-custom-node")
async def create_custom_node(request: CustomNodeRequest):
    """
    Create a custom workflow node
    
    This allows users to define custom processing steps for their workflows
    """
    try:
        logger.info(f"Creating custom node: {request.title}")
        
        # Create custom node
        custom_node = llm_integration.create_custom_node({
            'title': request.title,
            'node_type': request.node_type,
            'description': request.description,
            'params': request.params
        })
        
        return {
            "status": "success",
            "message": "Custom node created successfully",
            "node": custom_node,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to create custom node: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/examples")
async def get_examples():
    """Get example queries and their generated workflows"""
    examples = [
        {
            "query": "Generate AP aging report for last 90 days",
            "description": "Creates workflow to fetch vendor invoices, calculate aging, group by buckets, and generate branded report"
        },
        {
            "query": "Create AR register with outstanding amounts",
            "description": "Creates workflow to fetch customer invoices, calculate outstanding amounts, and generate register report"
        },
        {
            "query": "Show overdue invoices grouped by vendor",
            "description": "Creates workflow to filter overdue invoices, group by vendor, and generate summary report"
        },
        {
            "query": "Generate DSO analysis for Q4 2025",
            "description": "Creates workflow to calculate Days Sales Outstanding with custom date range"
        }
    ]
    
    return {
        "examples": examples,
        "description": "Example queries that demonstrate the LLM workflow generation capabilities"
    }


@app.get("/capabilities")
async def get_capabilities():
    """Get information about the LLM workflow generation capabilities"""
    return {
        "phase": "3.1 - Foundation & Data Integration",
        "capabilities": [
            "Natural language query processing",
            "Dynamic workflow generation",
            "Automatic node selection and sequencing",
            "Integration with existing data sources",
            "Custom node creation",
            "Workflow validation and optimization"
        ],
        "supported_reports": [
            "AP Aging",
            "AP Register", 
            "AP Overdue",
            "AR Aging",
            "AR Register",
            "AR Collection",
            "DSO Analysis"
        ],
        "data_sources": [
            "vendor_invoices",
            "customer_invoices",
            "payment_transactions",
            "master_data"
        ],
        "integration_points": [
            "InvoiceFetchNode",
            "GroupingNode", 
            "SummaryNode",
            "FilterNode",
            "SortNode",
            "BrandedExcelGeneratorNode"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_llm_workflow:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )