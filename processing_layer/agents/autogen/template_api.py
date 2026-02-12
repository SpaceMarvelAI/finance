"""
Template API
REST API endpoints for template management and workflow creation
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class TemplateConfig(BaseModel):
    """Template configuration model"""
    name: str
    category: str
    description: str
    version: str
    author: str
    workflow_structure: Dict[str, Any]
    parameters: List[Dict[str, Any]]


class TemplateApplication(BaseModel):
    """Template application model"""
    workflow_name: str
    company_id: str
    parameters: Dict[str, Any]
    schedule: Optional[Dict[str, Any]] = None
    notifications: Optional[Dict[str, Any]] = None


class TemplateAPI:
    """
    Template API Endpoints
    
    Provides REST API endpoints for:
    - Template management (CRUD operations)
    - Template application and workflow creation
    - Template preview and customization
    - Template analytics and usage statistics
    """
    
    def __init__(self, llm_config: Dict[str, Any]):
        self.llm_config = llm_config
        self.router = APIRouter()
        self.integration = None
        self.template_store = {}  # In-memory storage (would be database in production)
        
        # Initialize integration
        self._initialize_integration()
        
        # Register routes
        self._register_routes()
        
        # Load default templates
        self._load_default_templates()
    
    def _initialize_integration(self):
        """Initialize AutoGen integration"""
        try:
            from .autogen_integration import AutoGenIntegration
            self.integration = AutoGenIntegration(self.llm_config)
            logger.info("Template API initialized with integration")
        except ImportError as e:
            logger.error(f"Failed to initialize integration: {str(e)}")
            raise
    
    def _load_default_templates(self):
        """Load default templates into template store"""
        try:
            # AP Aging Report Template
            ap_aging_template = {
                "template_id": "ap_aging_report_v2",
                "name": "AP Aging Report with Analysis",
                "category": "Accounts Payable",
                "description": "Comprehensive AP aging analysis with vendor breakdown and trend analysis",
                "version": "2.1",
                "author": "FinanceAI Team",
                "metadata": {
                    "estimated_runtime": "2-5 minutes",
                    "data_requirements": ["vendor_invoices", "vendor_master"],
                    "complexity": "medium",
                    "industry_specific": False,
                    "company_size": ["small", "medium", "large"]
                },
                "workflow_structure": {
                    "nodes": [
                        {
                            "node_id": "data_retrieval_1",
                            "type": "data_retrieval",
                            "name": "Vendor Invoice Data",
                            "config": {
                                "data_source": "database",
                                "table": "vendor_invoices",
                                "filters": {
                                    "date_range": "last_90_days",
                                    "status": ["open", "partial"]
                                }
                            }
                        },
                        {
                            "node_id": "calculation_1",
                            "type": "aging_calculation",
                            "name": "Aging Buckets",
                            "config": {
                                "buckets": ["current", "1_30", "31_60", "61_90", "90_plus"],
                                "as_of_date": "today"
                            }
                        },
                        {
                            "node_id": "aggregation_1",
                            "type": "group_by",
                            "name": "Vendor Summary",
                            "config": {
                                "group_by": "vendor_name",
                                "metrics": ["count", "sum", "average_days"],
                                "sort_by": "sum_desc"
                            }
                        },
                        {
                            "node_id": "calculation_2",
                            "type": "financial_ratio",
                            "name": "AP Turnover",
                            "config": {
                                "formula": "total_purchases / average_ap",
                                "time_period": "last_12_months"
                            }
                        },
                        {
                            "node_id": "output_1",
                            "type": "excel_report",
                            "name": "AP Aging Report",
                            "config": {
                                "template": "ap_aging_template_v2",
                                "include_charts": True,
                                "chart_types": ["bar", "pie", "trend"],
                                "branding": "company_default"
                            }
                        }
                    ],
                    "connections": [
                        {
                            "from_node": "data_retrieval_1",
                            "to_node": "calculation_1",
                            "data_flow": "invoice_records"
                        },
                        {
                            "from_node": "calculation_1",
                            "to_node": "aggregation_1",
                            "data_flow": "aging_analysis"
                        },
                        {
                            "from_node": "aggregation_1",
                            "to_node": "calculation_2",
                            "data_flow": "vendor_summary"
                        },
                        {
                            "from_node": "calculation_2",
                            "to_node": "output_1",
                            "data_flow": "complete_analysis"
                        }
                    ]
                },
                "parameters": [
                    {
                        "param_id": "date_range",
                        "name": "Date Range",
                        "type": "select",
                        "default": "last_90_days",
                        "options": ["last_30_days", "last_90_days", "last_180_days", "custom"]
                    },
                    {
                        "param_id": "include_zero_balance",
                        "name": "Include Zero Balance",
                        "type": "boolean",
