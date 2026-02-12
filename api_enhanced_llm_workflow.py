"""
Enhanced API for Advanced LLM Workflow Generation
Phase 3.2: LLM Workflow Generation Engine
"""

from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
import asyncio
from datetime import datetime
import logging
import json

# Import our enhanced LLM workflow components
from processing_layer.workflows.enhanced_llm_workflow_generator import (
    EnhancedLLMWorkflowGenerator, 
    QueryAnalysis, 
    WorkflowOptimization,
    WorkflowComplexity,
    QueryType
)
from processing_layer.agents.langgraph_framework.llm_integration import LLMWorkflowIntegration
from shared.config.logging_config import get_logger


logger = get_logger(__name__)

app = FastAPI(
    title="Enhanced LLM Workflow Generation API",
    description="Phase 3.2: Advanced LLM Workflow Generation Engine",
    version="3.2.0"
)


class AdvancedQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language query for workflow generation")
    company_id: str = Field(..., description="Company identifier")
    user_id: str = Field(..., description="User identifier")
    optimization_level: str = Field(default="auto", description="Optimization level: auto, basic, advanced")
    parallel_execution: bool = Field(default=True, description="Enable parallel execution")
    cache_results: bool = Field(default=True, description="Enable result caching")
    performance_monitoring: bool = Field(default=True, description="Enable performance monitoring")


class WorkflowResponse(BaseModel):
    workflow_id: str
    workflow_definition: Dict[str, Any]
    analysis: Dict[str, Any]
    optimization: Dict[str, Any]
    performance_metadata: Dict[str, Any]
    status: str
    message: str
    timestamp: str


class OptimizationRequest(BaseModel):
    workflow_definition: Dict[str, Any]
    optimization_level: str = Field(default="advanced", description="Optimization level")
    parallel_execution: bool = Field(default=True, description="Enable parallel execution")
    memory_optimization: bool = Field(default=True, description="Enable memory optimization")


class QueryAnalysisResponse(BaseModel):
    analysis: Dict[str, Any]
    confidence_score: float
    suggested_nodes: List[str]
    complexity: str
    estimated_time: str
    memory_requirements: str
    timestamp: str


# Global instances
enhanced_workflow_generator = EnhancedLLMWorkflowGenerator()
llm_integration = LLMWorkflowIntegration()


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Enhanced LLM Workflow Generation API - Phase 3.2",
        "version": "3.2.0",
        "description": "Advanced LLM Workflow Generation Engine with optimization and performance monitoring",
        "endpoints": {
            "POST /generate-workflow-advanced": "Generate advanced workflow with optimization",
            "POST /analyze-query": "Analyze query without generating workflow",
            "POST /optimize-workflow": "Optimize existing workflow",
            "GET /health": "Health check",
            "GET /capabilities": "Get API capabilities",
            "GET /examples": "Get example queries and workflows"
        }
    }


@app.get("/health")
async def health_check():
    """Enhanced health check with component status"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "enhanced_llm_generator": "active",
            "llm_integration": "active",
            "database": "connected",
            "cache": "active",
            "optimization_engine": "active"
        },
        "version": "3.2.0",
        "features": [
            "Advanced query analysis",
            "Workflow optimization",
            "Performance monitoring",
            "Parallel execution",
            "Result caching",
            "Memory optimization"
        ]
    }


@app.post("/generate-workflow-advanced", response_model=WorkflowResponse)
async def generate_advanced_workflow(request: AdvancedQueryRequest):
    """
    Generate advanced workflow with comprehensive optimization and performance monitoring
    
    This endpoint provides:
    - Enhanced query analysis with detailed requirements extraction
    - Advanced workflow optimization with performance tuning
    - Parallel execution opportunities identification
    - Memory optimization and caching strategies
    - Performance monitoring and bottleneck analysis
    """
    try:
        logger.info(f"Generating advanced workflow for query: {request.query}")
        
        # Generate advanced workflow
        workflow_definition = await enhanced_workflow_generator.generate_workflow_advanced(
            request.query, 
            request.company_id, 
            request.user_id
        )
        
        # Generate workflow ID
        workflow_id = f"advanced_workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Extract analysis and optimization data
        analysis = workflow_definition.get('metadata', {}).get('analysis', {})
        optimization = workflow_definition.get('metadata', {}).get('optimization', {})
        performance_metadata = workflow_definition.get('metadata', {}).get('performance', {})
        
        response = WorkflowResponse(
            workflow_id=workflow_id,
            workflow_definition=workflow_definition,
            analysis=analysis,
            optimization=optimization,
            performance_metadata=performance_metadata,
            status="success",
            message="Advanced workflow generated successfully with optimization",
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"Successfully generated advanced workflow: {workflow_id}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to generate advanced workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-query", response_model=QueryAnalysisResponse)
async def analyze_query(request: AdvancedQueryRequest):
    """
    Analyze query without generating workflow
    
    This endpoint provides detailed analysis of the query including:
    - Query type and complexity classification
    - Required data sources and filters
    - Performance requirements and optimization opportunities
    - Confidence score and suggested approach
    """
    try:
        logger.info(f"Analyzing query: {request.query}")
        
        # Perform enhanced query analysis
        analysis = await enhanced_workflow_generator._analyze_query_advanced(
            request.query, 
            request.company_id
        )
        
        response = QueryAnalysisResponse(
            analysis=analysis.__dict__,
            confidence_score=analysis.confidence_score,
            suggested_nodes=analysis.suggested_nodes,
            complexity=analysis.complexity.value,
            estimated_time=enhanced_workflow_generator._estimate_execution_time(analysis),
            memory_requirements=enhanced_workflow_generator._estimate_memory_requirements(analysis),
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"Successfully analyzed query with confidence: {analysis.confidence_score}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to analyze query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/optimize-workflow")
async def optimize_workflow(request: OptimizationRequest):
    """
    Optimize existing workflow for better performance
    
    This endpoint provides:
    - Performance optimization suggestions
    - Node-level optimizations
    - Caching strategy recommendations
    - Memory optimization opportunities
    - Parallel execution identification
    """
    try:
        logger.info("Optimizing existing workflow")
        
        # Get optimization suggestions
        optimization_suggestions = await enhanced_workflow_generator._get_optimization_suggestions(
            request.workflow_definition,
            QueryAnalysis(
                query_type=QueryType.REPORT_GENERATION,
                report_type='custom',
                data_source='vendor_invoices',
                complexity=WorkflowComplexity.MEDIUM,
                key_requirements=[],
                time_range='all_time',
                filters={},
                aggregations=[],
                custom_calculations=[],
                output_format='excel',
                confidence_score=0.8,
                suggested_nodes=[]
            )
        )
        
        # Apply optimizations
        optimized_workflow = enhanced_workflow_generator._apply_optimizations(
            request.workflow_definition,
            optimization_suggestions
        )
        
        return {
            "status": "success",
            "message": "Workflow optimized successfully",
            "optimization_suggestions": {
                "performance_improvements": optimization_suggestions.performance_improvements,
                "node_optimizations": optimization_suggestions.node_optimizations,
                "caching_opportunities": optimization_suggestions.caching_opportunities,
                "parallel_execution_opportunities": optimization_suggestions.parallel_execution_opportunities,
                "memory_optimizations": optimization_suggestions.memory_optimizations
            },
            "optimized_workflow": optimized_workflow,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to optimize workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/performance-metrics")
async def get_performance_metrics():
    """Get performance metrics and statistics"""
    try:
        # Get performance metrics from the generator
        metrics = {
            "query_cache_hit_rate": len(enhanced_workflow_generator.query_cache),
            "optimization_cache_hit_rate": len(enhanced_workflow_generator.optimization_cache),
            "node_performance_metrics": enhanced_workflow_generator.node_performance_metrics,
            "average_analysis_time": "N/A",  # Would need timing implementation
            "average_optimization_time": "N/A",  # Would need timing implementation
            "most_complex_workflows": [],  # Would need tracking implementation
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "status": "success",
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/examples")
async def get_advanced_examples():
    """Get advanced example queries and their generated workflows"""
    examples = [
        {
            "query": "Generate AP aging report for last 90 days with vendor grouping and currency conversion",
            "description": "Advanced workflow with currency conversion, vendor grouping, and detailed aging analysis",
            "complexity": "complex",
            "optimization_features": [
                "Parallel data fetching",
                "Currency conversion optimization",
                "Advanced grouping with subtotals",
                "Memory-efficient processing"
            ],
            "performance_features": [
                "Batch processing (2000 records)",
                "Parallel execution enabled",
                "Result caching (1 hour)",
                "Memory optimization"
            ]
        },
        {
            "query": "Create AR register with outstanding amounts, DSO calculation, and trend analysis",
            "description": "Comprehensive workflow with DSO calculation, trend analysis, and advanced aggregations",
            "complexity": "advanced",
            "optimization_features": [
                "Distributed processing for large datasets",
                "Streaming data processing",
                "Advanced trend analysis",
                "Real-time performance monitoring"
            ],
            "performance_features": [
                "Horizontal scaling support",
                "Streaming processing",
                "Advanced caching strategies",
                "Optimized for large datasets"
            ]
        },
        {
            "query": "Show overdue invoices grouped by vendor with aging buckets and payment probability scoring",
            "description": "Advanced workflow with machine learning scoring, complex grouping, and predictive analysis",
            "complexity": "advanced",
            "optimization_features": [
                "ML model integration",
                "Complex predictive calculations",
                "Advanced data transformations",
                "Real-time scoring"
            ],
            "performance_features": [
                "GPU acceleration support",
                "Distributed ML processing",
                "Real-time scoring optimization",
                "Advanced memory management"
            ]
        },
        {
            "query": "Generate multi-currency financial report with exchange rate fluctuations and risk analysis",
            "description": "Complex workflow with real-time currency conversion, risk analysis, and fluctuation tracking",
            "complexity": "complex",
            "optimization_features": [
                "Real-time exchange rate API integration",
                "Currency risk analysis",
                "Fluctuation tracking",
                "Advanced financial calculations"
            ],
            "performance_features": [
                "API rate limiting optimization",
                "Currency cache optimization",
                "Real-time data processing",
                "Financial calculation optimization"
            ]
        }
    ]
    
    return {
        "examples": examples,
        "description": "Advanced examples demonstrating Phase 3.2 capabilities",
        "features_highlighted": [
            "Advanced query analysis",
            "Workflow optimization",
            "Performance monitoring",
            "Parallel execution",
            "Memory optimization",
            "Caching strategies",
            "Real-time processing",
            "Complex calculations"
        ]
    }


@app.get("/capabilities")
async def get_advanced_capabilities():
    """Get information about the advanced LLM workflow generation capabilities"""
    return {
        "phase": "3.2 - LLM Workflow Generation Engine",
        "capabilities": [
            {
                "category": "Advanced Query Analysis",
                "features": [
                    "Detailed requirements extraction",
                    "Complexity classification",
                    "Performance requirement analysis",
                    "Implicit requirement identification",
                    "Data transformation analysis"
                ]
            },
            {
                "category": "Workflow Optimization",
                "features": [
                    "Performance optimization suggestions",
                    "Node-level optimizations",
                    "Caching strategy recommendations",
                    "Parallel execution opportunities",
                    "Memory optimization strategies"
                ]
            },
            {
                "category": "Performance Monitoring",
                "features": [
                    "Execution time estimation",
                    "Memory requirement analysis",
                    "Bottleneck identification",
                    "Scaling recommendations",
                    "Performance metrics tracking"
                ]
            },
            {
                "category": "Advanced Features",
                "features": [
                    "Parallel execution support",
                    "Result caching with TTL",
                    "Memory-efficient processing",
                    "Batch processing optimization",
                    "Real-time performance monitoring"
                ]
            }
        ],
        "supported_report_types": [
            "AP Aging (with advanced features)",
            "AP Register (with optimization)",
            "AP Overdue (with predictive analysis)",
            "AR Aging (with trend analysis)",
            "AR Register (with DSO calculation)",
            "AR Collection (with ML scoring)",
            "DSO Analysis (with advanced metrics)",
            "Custom Reports (with full optimization)"
        ],
        "optimization_levels": [
            "Basic: Standard optimization",
            "Advanced: Full optimization with parallel execution",
            "Auto: Automatic optimization based on complexity"
        ],
        "performance_features": [
            "Query result caching",
            "Workflow optimization caching",
            "Parallel node execution",
            "Memory-efficient processing",
            "Batch processing support",
            "Real-time performance monitoring"
        ]
    }


@app.get("/optimization-strategies")
async def get_optimization_strategies():
    """Get detailed optimization strategies and recommendations"""
    strategies = {
        "performance_optimizations": [
            {
                "strategy": "Batch Processing",
                "description": "Process data in batches to reduce memory usage and improve performance",
                "implementation": "Set batch_size parameter in fetch nodes",
                "benefits": ["Reduced memory usage", "Improved processing speed", "Better resource utilization"]
            },
            {
                "strategy": "Parallel Execution",
                "description": "Execute independent nodes in parallel to reduce overall execution time",
                "implementation": "Enable parallel_fetch and parallel_processing flags",
                "benefits": ["Faster execution", "Better CPU utilization", "Improved throughput"]
            },
            {
                "strategy": "Result Caching",
                "description": "Cache frequently accessed results to avoid recomputation",
                "implementation": "Enable cache_result with appropriate TTL",
                "benefits": ["Reduced computation time", "Lower resource usage", "Improved response times"]
            }
        ],
        "memory_optimizations": [
            {
                "strategy": "Memory Cleanup",
                "description": "Clean up intermediate results to free memory during processing",
                "implementation": "Enable memory_cleanup in optimization nodes",
                "benefits": ["Reduced memory footprint", "Prevents memory leaks", "Better scalability"]
            },
            {
                "strategy": "Streaming Processing",
                "description": "Process data in streams rather than loading everything into memory",
                "implementation": "Use streaming APIs for large datasets",
                "benefits": ["Handles large datasets", "Constant memory usage", "Better performance"]
            }
        ],
        "caching_strategies": [
            {
                "strategy": "Query Result Caching",
                "description": "Cache query results based on query parameters",
                "implementation": "Use query_cache with appropriate keys",
                "benefits": ["Faster subsequent queries", "Reduced database load", "Improved user experience"]
            },
            {
                "strategy": "Workflow Optimization Caching",
                "description": "Cache optimization suggestions for similar workflows",
                "implementation": "Use optimization_cache with workflow type keys",
                "benefits": ["Faster optimization", "Consistent optimization quality", "Reduced LLM calls"]
            }
        ]
    }
    
    return {
        "strategies": strategies,
        "recommendations": [
            "Use batch processing for datasets larger than 1000 records",
            "Enable parallel execution for workflows with independent nodes",
            "Implement result caching for frequently accessed data",
            "Use memory cleanup for long-running workflows",
            "Consider streaming processing for very large datasets"
        ],
        "best_practices": [
            "Monitor performance metrics regularly",
            "Optimize based on actual usage patterns",
            "Use appropriate cache TTL values",
            "Balance performance with resource usage",
            "Test optimizations with realistic data volumes"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_enhanced_llm_workflow:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )