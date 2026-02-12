"""
MCP Server Implementation for Financial Automation System
Provides MCP tools and resources for report generation and management
"""

import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.getcwd())

# Import MCP tools
from mcp.tools.report_generation_tools import report_tools, TOOLS, get_tool_function

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MCPServer:
    """
    MCP Server for Financial Automation System
    """
    
    def __init__(self, config_path: str = "./mcp/server_config.json"):
        self.config_path = config_path
        self.config = self.load_config()
        self.tools = self.initialize_tools()
        self.resources = self.initialize_resources()
        
        logger.info(f"MCP Server initialized with {len(self.tools)} tools")
    
    def load_config(self) -> Dict[str, Any]:
        """Load MCP server configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "server": {
                "name": "financial-automation-mcp",
                "version": "1.0.0",
                "description": "MCP server for Financial Automation System"
            },
            "tools": {
                "enabled": True,
                "categories": []
            },
            "resources": {
                "enabled": True,
                "categories": []
            }
        }
    
    def initialize_tools(self) -> Dict[str, Any]:
        """Initialize MCP tools"""
        tools = {}
        
        if self.config.get("tools", {}).get("enabled", False):
            for category in self.config.get("tools", {}).get("categories", []):
                for tool in category.get("tools", []):
                    tool_name = tool.get("name")
                    if tool_name:
                        tools[tool_name] = {
                            "description": tool.get("description", ""),
                            "function": get_tool_function(tool_name),
                            "parameters": tool.get("parameters", {})
                        }
        
        return tools
    
    def initialize_resources(self) -> Dict[str, Any]:
        """Initialize MCP resources"""
        resources = {}
        
        if self.config.get("resources", {}).get("enabled", False):
            for category in self.config.get("resources", {}).get("categories", []):
                for resource in category.get("resources", []):
                    resource_name = resource.get("name")
                    if resource_name:
                        resources[resource_name] = {
                            "description": resource.get("description", ""),
                            "uri": resource.get("uri", ""),
                            "type": resource.get("type", "file")
                        }
        
        return resources
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools"""
        return [
            {
                "name": name,
                "description": info["description"],
                "parameters": info["parameters"]
            }
            for name, info in self.tools.items()
        ]
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """Get list of available resources"""
        return [
            {
                "name": name,
                "description": info["description"],
                "uri": info["uri"],
                "type": info["type"]
            }
            for name, info in self.resources.items()
        ]
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool"""
        try:
            if tool_name not in self.tools:
                return {
                    "status": "error",
                    "message": f"Tool not found: {tool_name}"
                }
            
            tool_info = self.tools[tool_name]
            function = tool_info["function"]
            
            # Execute the tool function
            result = function(**arguments)
            
            return result
            
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool"""
        if tool_name in self.tools:
            return {
                "name": tool_name,
                "description": self.tools[tool_name]["description"],
                "parameters": self.tools[tool_name]["parameters"]
            }
        return None
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information"""
        return {
            "name": self.config.get("server", {}).get("name", "financial-automation-mcp"),
            "version": self.config.get("server", {}).get("version", "1.0.0"),
            "description": self.config.get("server", {}).get("description", ""),
            "tools_count": len(self.tools),
            "resources_count": len(self.resources),
            "timestamp": datetime.now().isoformat()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            # Test basic functionality
            test_result = report_tools.get_available_templates()
            
            return {
                "status": "healthy" if test_result["status"] == "success" else "unhealthy",
                "tools_available": len(self.tools),
                "resources_available": len(self.resources),
                "test_result": test_result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Global MCP server instance
mcp_server = MCPServer()


def get_mcp_server():
    """Get the global MCP server instance"""
    return mcp_server


# MCP Tool Functions (for direct access)
def get_available_templates():
    """Get list of available report templates"""
    return mcp_server.execute_tool("get_available_templates", {})


def get_template_info(template_type: str):
    """Get detailed information about a specific template"""
    return mcp_server.execute_tool("get_template_info", {"template_type": template_type})


def generate_report(template_type: str, report_data: Dict[str, Any], company_id: str, params: Optional[Dict[str, Any]] = None):
    """Generate a report using the specified template"""
    return mcp_server.execute_tool("generate_report", {
        "template_type": template_type,
        "report_data": report_data,
        "company_id": company_id,
        "params": params or {}
    })


def validate_template_config(template_type: str, config: Dict[str, Any]):
    """Validate template configuration"""
    return mcp_server.execute_tool("validate_template_config", {
        "template_type": template_type,
        "config": config
    })


def list_generated_reports(company_id: Optional[str] = None, limit: int = 50):
    """List recently generated reports"""
    return mcp_server.execute_tool("list_generated_reports", {
        "company_id": company_id,
        "limit": limit
    })


def get_report_metadata(filename: str):
    """Get metadata for a specific report file"""
    return mcp_server.execute_tool("get_report_metadata", {"filename": filename})


def delete_report(filename: str):
    """Delete a generated report file"""
    return mcp_server.execute_tool("delete_report", {"filename": filename})


def get_system_status():
    """Get overall system status and statistics"""
    return mcp_server.execute_tool("get_system_status", {})


# MCP Tool Registry
MCP_TOOLS = {
    "get_available_templates": {
        "function": get_available_templates,
        "description": "Get list of available report templates with their capabilities",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "get_template_info": {
        "function": get_template_info,
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
        "function": generate_report,
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
        "function": validate_template_config,
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
        "function": list_generated_reports,
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
        "function": get_report_metadata,
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
        "function": delete_report,
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
        "function": get_system_status,
        "description": "Get overall system status and statistics",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}


if __name__ == "__main__":
    # Test the MCP server
    server = MCPServer()
    
    print("🧪 Testing MCP Server")
    print("=" * 50)
    
    # Test server info
    print("\n1. Server Info:")
    info = server.get_server_info()
    print(f"   Name: {info['name']}")
    print(f"   Version: {info['version']}")
    print(f"   Tools: {info['tools_count']}")
    print(f"   Resources: {info['resources_count']}")
    
    # Test health check
    print("\n2. Health Check:")
    health = server.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Tools Available: {health['tools_available']}")
    
    # Test tools
    print("\n3. Available Tools:")
    tools = server.get_tools()
    for tool in tools:
        print(f"   - {tool['name']}: {tool['description']}")
    
    # Test resources
    print("\n4. Available Resources:")
    resources = server.get_resources()
    for resource in resources:
        print(f"   - {resource['name']}: {resource['description']}")
    
    print("\n✅ MCP Server is ready!")