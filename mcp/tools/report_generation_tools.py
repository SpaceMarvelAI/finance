"""
MCP Tools for Report Generation and Management
Provides tools for the MCP server to interact with the LangGraph report generation system
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import logging

# Import our LangGraph integration
from processing_layer.agents.langgraph_framework.report_template_integration import ReportTemplateIntegration
from data_layer.database.database_manager import get_database
from shared.config.logging_config import get_logger

logger = get_logger(__name__)


class ReportGenerationTools:
    """
    MCP Tools for report generation and management
    """
    
    def __init__(self):
        self.report_integration = ReportTemplateIntegration()
        self.db_manager = get_database()
    
    def get_available_templates(self) -> Dict[str, Any]:
        """
        Get list of available report templates
        
        Returns:
            Dict containing template information
        """
        try:
            templates = self.report_integration.get_available_templates()
            capabilities = self.report_integration.get_template_capabilities()
            
            return {
                "status": "success",
                "templates": templates,
                "capabilities": capabilities,
                "count": len(templates)
            }
        except Exception as e:
            logger.error(f"Failed to get available templates: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_template_info(self, template_type: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific template
        
        Args:
            template_type: Type of template (e.g., 'ap_aging', 'ap_register')
            
        Returns:
            Dict containing template details
        """
        try:
            template_info = self.report_integration.get_template_info(template_type)
            
            return {
                "status": "success",
                "template_type": template_type,
                "info": template_info
            }
        except Exception as e:
            logger.error(f"Failed to get template info for {template_type}: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def generate_report(self, template_type: str, report_data: Dict[str, Any], company_id: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a report using the specified template
        
        Args:
            template_type: Type of report template
            report_data: Data to use for report generation
            company_id: Company ID for branding
            params: Additional parameters
            
        Returns:
            Dict containing generation result
        """
        try:
            # Validate inputs
            if not template_type:
                return {
                    "status": "error",
                    "message": "Template type is required"
                }
            
            if not company_id:
                return {
                    "status": "error", 
                    "message": "Company ID is required"
                }
            
            # Generate report
            result = self.report_integration.generate_report(
                template_type=template_type,
                report_data=report_data,
                company_id=company_id,
                params=params or {}
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def validate_template_config(self, template_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate template configuration
        
        Args:
            template_type: Type of template
            config: Configuration to validate
            
        Returns:
            Dict containing validation result
        """
        try:
            errors = self.report_integration.validate_template_config(template_type, config)
            
            return {
                "status": "success",
                "valid": len(errors) == 0,
                "errors": errors
            }
        except Exception as e:
            logger.error(f"Failed to validate template config: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def list_generated_reports(self, company_id: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        """
        List recently generated reports
        
        Args:
            company_id: Filter by company ID
            limit: Maximum number of reports to return
            
        Returns:
            Dict containing list of reports
        """
        try:
            reports_dir = Path("./output/reports")
            
            if not reports_dir.exists():
                return {
                    "status": "success",
                    "reports": [],
                    "count": 0
                }
            
            # Get all Excel files
            report_files = list(reports_dir.glob("*.xlsx"))
            
            # Filter by company if specified
            if company_id:
                report_files = [
                    f for f in report_files 
                    if company_id in f.name
                ]
            
            # Sort by modification time (newest first)
            report_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Limit results
            report_files = report_files[:limit]
            
            reports = []
            for file_path in report_files:
                stat = file_path.stat()
                reports.append({
                    "filename": file_path.name,
                    "file_path": str(file_path),
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            
            return {
                "status": "success",
                "reports": reports,
                "count": len(reports)
            }
            
        except Exception as e:
            logger.error(f"Failed to list generated reports: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_report_metadata(self, filename: str) -> Dict[str, Any]:
        """
        Get metadata for a specific report file
        
        Args:
            filename: Name of the report file
            
        Returns:
            Dict containing report metadata
        """
        try:
            file_path = Path("./output/reports") / filename
            
            if not file_path.exists():
                return {
                    "status": "error",
                    "message": f"Report file not found: {filename}"
                }
            
            stat = file_path.stat()
            
            return {
                "status": "success",
                "metadata": {
                    "filename": filename,
                    "file_path": str(file_path),
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get report metadata for {filename}: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def delete_report(self, filename: str) -> Dict[str, Any]:
        """
        Delete a generated report file
        
        Args:
            filename: Name of the report file to delete
            
        Returns:
            Dict containing deletion result
        """
        try:
            file_path = Path("./output/reports") / filename
            
            if not file_path.exists():
                return {
                    "status": "error",
                    "message": f"Report file not found: {filename}"
                }
            
            file_path.unlink()
            
            return {
                "status": "success",
                "message": f"Report deleted successfully: {filename}"
            }
            
        except Exception as e:
            logger.error(f"Failed to delete report {filename}: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get system status and statistics
        
        Returns:
            Dict containing system status
        """
        try:
            # Get template information
            templates = self.report_integration.get_available_templates()
            capabilities = self.report_integration.get_template_capabilities()
            
            # Get report statistics
            reports_result = self.list_generated_reports(limit=1000)
            
            # Get database status
            try:
                db_status = "connected" if self.db_manager.conn else "disconnected"
            except:
                db_status = "unknown"
            
            return {
                "status": "success",
                "system": {
                    "report_templates": {
                        "count": len(templates),
                        "available": templates,
                        "capabilities": capabilities
                    },
                    "generated_reports": {
                        "count": reports_result.get("count", 0),
                        "total_size": sum(r.get("size", 0) for r in reports_result.get("reports", []))
                    },
                    "database": {
                        "status": db_status
                    },
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {
                "status": "error",
                "message": str(e)
            }


# Create global instance
report_tools = ReportGenerationTools()


# MCP Tool Definitions
TOOLS = {
    "get_available_templates": {
        "description": "Get list of available report templates with their capabilities",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "get_template_info": {
        "description": "Get detailed information about a specific report template",
        "parameters": {
            "type": "object",
            "properties": {
                "template_type": {
                    "type": "string",
                    "description": "Type of template (e.g., 'ap_aging', 'ap_register', 'ar_aging', 'ar_register')"
                }
            },
            "required": ["template_type"]
        }
    },
    "generate_report": {
        "description": "Generate a report using the specified template and data",
        "parameters": {
            "type": "object",
            "properties": {
                "template_type": {
                    "type": "string",
                    "description": "Type of report template to use"
                },
                "report_data": {
                    "type": "object",
                    "description": "Data to use for report generation"
                },
                "company_id": {
                    "type": "string",
                    "description": "Company ID for branding and configuration"
                },
                "params": {
                    "type": "object",
                    "description": "Additional parameters for report generation",
                    "properties": {
                        "as_of_date": {
                            "type": "string",
                            "description": "As-of date for the report"
                        }
                    },
                    "required": []
                }
            },
            "required": ["template_type", "report_data", "company_id"]
        }
    },
    "validate_template_config": {
        "description": "Validate template configuration before report generation",
        "parameters": {
            "type": "object",
            "properties": {
                "template_type": {
                    "type": "string",
                    "description": "Type of template to validate"
                },
                "config": {
                    "type": "object",
                    "description": "Configuration to validate"
                }
            },
            "required": ["template_type", "config"]
        }
    },
    "list_generated_reports": {
        "description": "List recently generated reports with metadata",
        "parameters": {
            "type": "object",
            "properties": {
                "company_id": {
                    "type": "string",
                    "description": "Filter reports by company ID (optional)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of reports to return (default: 50)"
                }
            },
            "required": []
        }
    },
    "get_report_metadata": {
        "description": "Get metadata for a specific report file",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Name of the report file"
                }
            },
            "required": ["filename"]
        }
    },
    "delete_report": {
        "description": "Delete a generated report file",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Name of the report file to delete"
                }
            },
            "required": ["filename"]
        }
    },
    "get_system_status": {
        "description": "Get overall system status and statistics",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}


def get_tool_function(tool_name: str):
    """Get the function for a specific tool"""
    if tool_name == "get_available_templates":
        return report_tools.get_available_templates
    elif tool_name == "get_template_info":
        return report_tools.get_template_info
    elif tool_name == "generate_report":
        return report_tools.generate_report
    elif tool_name == "validate_template_config":
        return report_tools.validate_template_config
    elif tool_name == "list_generated_reports":
        return report_tools.list_generated_reports
    elif tool_name == "get_report_metadata":
        return report_tools.get_report_metadata
    elif tool_name == "delete_report":
        return report_tools.delete_report
    elif tool_name == "get_system_status":
        return report_tools.get_system_status
    else:
        raise ValueError(f"Unknown tool: {tool_name}")