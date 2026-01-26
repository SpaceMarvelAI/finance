"""
PRODUCTION CONFIGURATION MANAGEMENT
Database-driven, no hardcoding
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from pathlib import Path


class ConfigurationManager:
    """
    Centralized configuration management
    
    In production:
    - Load from database
    - Cache configurations
    - Support versioning
    - Hot reload capability
    """
    
    def __init__(self, config_source: str = "database"):
        """
        Initialize configuration manager
        
        Args:
            config_source: "database", "file", "api"
        """
        self.config_source = config_source
        self.cache = {}
        self.version = "1.0.0"
    
    def get_report_config(self, report_type: str, org_id: str = "default") -> Dict[str, Any]:
        """
        Get configuration for a report type
        
        Args:
            report_type: Type of report
            org_id: Organization ID (for multi-tenancy)
            
        Returns:
            Report configuration
        """
        cache_key = f"{org_id}:{report_type}"
        
        # Check cache
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Load from source
        if self.config_source == "database":
            config = self._load_from_database(report_type, org_id)
        elif self.config_source == "file":
            config = self._load_from_file(report_type, org_id)
        else:
            config = self._get_default_config(report_type)
        
        # Cache it
        self.cache[cache_key] = config
        
        return config
    
    def get_node_config(self, node_type: str, org_id: str = "default") -> Dict[str, Any]:
        """
        Get configuration for a node
        
        Args:
            node_type: Type of node
            org_id: Organization ID
            
        Returns:
            Node configuration
        """
        # In production: load from database
        return self._get_default_node_config(node_type, org_id)
    
    def get_workflow_config(self, workflow_id: str, org_id: str = "default") -> Dict[str, Any]:
        """
        Get workflow configuration
        
        Args:
            workflow_id: Workflow ID
            org_id: Organization ID
            
        Returns:
            Workflow configuration
        """
        # In production: load from workflows table
        return self._load_workflow(workflow_id, org_id)
    
    def get_rules_config(self, rule_set: str, org_id: str = "default") -> Dict[str, Any]:
        """
        Get rules configuration
        
        Args:
            rule_set: Rule set name
            org_id: Organization ID
            
        Returns:
            Rules configuration
        """
        # In production: load from rules table
        return self._load_rules(rule_set, org_id)
    
    def _load_from_database(self, report_type: str, org_id: str) -> Dict[str, Any]:
        """Load configuration from database"""
        # TODO: Implement database loading
        # For now, return defaults
        return self._get_default_config(report_type)
    
    def _load_from_file(self, report_type: str, org_id: str) -> Dict[str, Any]:
        """Load configuration from file"""
        config_path = Path(f"./configs/{org_id}/{report_type}.json")
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        
        return self._get_default_config(report_type)
    
    def _load_workflow(self, workflow_id: str, org_id: str) -> Dict[str, Any]:
        """Load workflow from database"""
        # TODO: Query workflows table
        return {}
    
    def _load_rules(self, rule_set: str, org_id: str) -> Dict[str, Any]:
        """Load rules from database"""
        # TODO: Query rules table
        return {"rules": []}
    
    def _get_default_config(self, report_type: str) -> Dict[str, Any]:
        """Get default configuration for report type"""
        
        configs = {
            "ap_aging": {
                "report_type": "ap_aging",
                "data_source": "invoices",
                "pipeline": [
                    "fetch_invoices",
                    "calculate_outstanding",
                    "calculate_aging",
                    "filter_by_status",
                    "group_data",
                    "calculate_summary",
                    "generate_output"
                ],
                "nodes": {
                    "fetch_invoices": {
                        "node_type": "InvoiceFetchNode",
                        "params": {"category": "purchase"}
                    },
                    "calculate_outstanding": {
                        "node_type": "OutstandingCalculatorNode"
                    },
                    "calculate_aging": {
                        "node_type": "AgingCalculatorNode"
                    },
                    "filter_by_status": {
                        "node_type": "FilterNode",
                        "params": {
                            "conditions": [
                                {"field": "status", "operator": "in", "value": ["unpaid", "partially_paid"]}
                            ]
                        }
                    },
                    "group_data": {
                        "node_type": "GroupingNode",
                        "params": {"group_by": "aging_bucket"}
                    },
                    "calculate_summary": {
                        "node_type": "SummaryNode"
                    },
                    "generate_output": {
                        "node_type": "ExcelGeneratorNode"
                    }
                },
                "settings": {
                    "aging_buckets": [30, 60, 90],
                    "include_paid": False,
                    "currency": "INR"
                }
            },
            
            "ar_collection": {
                "report_type": "ar_collection",
                "pipeline": [
                    "fetch_invoices",
                    "calculate_aging",
                    "check_sla",
                    "calculate_priority",
                    "apply_rules",
                    "sort_by_priority",
                    "generate_output"
                ],
                "nodes": {
                    "fetch_invoices": {
                        "node_type": "InvoiceFetchNode",
                        "params": {"category": "sales"}
                    },
                    "calculate_aging": {
                        "node_type": "AgingCalculatorNode"
                    },
                    "check_sla": {
                        "node_type": "SLACheckerNode",
                        "params": {"sla_days": 30}
                    },
                    "calculate_priority": {
                        "node_type": "CustomCalculationNode",
                        "params": {
                            "formula": "outstanding * aging_days * sla_multiplier"
                        }
                    },
                    "apply_rules": {
                        "node_type": "RuleEngineNode",
                        "params": {
                            "rule_set": "collection_priority"
                        }
                    },
                    "sort_by_priority": {
                        "node_type": "SortNode",
                        "params": {
                            "sort_by": [{"field": "priority_score", "order": "desc"}]
                        }
                    },
                    "generate_output": {
                        "node_type": "ExcelGeneratorNode"
                    }
                },
                "settings": {
                    "sla_days": 30,
                    "priority_weights": {
                        "amount": 1.0,
                        "age": 1.0,
                        "sla": 2.0
                    }
                }
            }
        }
        
        return configs.get(report_type, {})
    
    def _get_default_node_config(self, node_type: str, org_id: str) -> Dict[str, Any]:
        """Get default node configuration"""
        
        # Organization-specific overrides
        org_configs = {
            "default": {
                "AgingCalculatorNode": {
                    "aging_buckets": [30, 60, 90],
                    "as_of_date_mode": "current"
                },
                "SLACheckerNode": {
                    "sla_days": 30,
                    "business_days_only": False
                },
                "DuplicateDetectorNode": {
                    "tolerance": 0.01,
                    "min_confidence": 75
                }
            }
        }
        
        return org_configs.get(org_id, {}).get(node_type, {})


class WorkflowBuilder:
    """
    Build workflows from high-level specifications
    No hardcoding
    """
    
    def __init__(self, config_manager: ConfigurationManager):
        self.config_mgr = config_manager
    
    def build_workflow(self, intent: Dict[str, Any], org_id: str = "default") -> Dict[str, Any]:
        """
        Build workflow from parsed intent
        
        Args:
            intent: Parsed user intent
                {
                    "report_type": "ap_aging",
                    "filters": {...},
                    "output_format": "excel"
                }
            org_id: Organization ID
            
        Returns:
            Workflow configuration
        """
        report_type = intent.get('report_type')
        filters = intent.get('filters', {})
        output_format = intent.get('output_format', 'excel')
        
        # Get base config for report type
        base_config = self.config_mgr.get_report_config(report_type, org_id)
        
        if not base_config:
            return None
        
        # Apply filters to configuration
        modified_config = self._apply_filters(base_config, filters)
        
        # Set output format
        modified_config = self._set_output_format(modified_config, output_format)
        
        return modified_config
    
    def _apply_filters(self, config: Dict, filters: Dict) -> Dict:
        """
        Apply runtime filters to configuration
        
        Args:
            config: Base configuration
            filters: Runtime filters
            
        Returns:
            Modified configuration
        """
        config = config.copy()
        
        # Find filter node in pipeline
        if 'nodes' in config:
            for node_name, node_config in config['nodes'].items():
                if node_config['node_type'] == 'FilterNode':
                    # Add/modify filter conditions
                    conditions = node_config.get('params', {}).get('conditions', [])
                    
                    # Add new conditions from filters
                    for field, value in filters.items():
                        if field == 'date_from' or field == 'date_to':
                            continue  # Handle separately
                        
                        # Add condition
                        conditions.append({
                            "field": field,
                            "operator": self._infer_operator(value),
                            "value": value
                        })
                    
                    node_config['params']['conditions'] = conditions
        
        return config
    
    def _set_output_format(self, config: Dict, output_format: str) -> Dict:
        """
        Set output format in configuration
        
        Args:
            config: Configuration
            output_format: Desired format
            
        Returns:
            Modified configuration
        """
        config = config.copy()
        
        # Map format to node type
        format_map = {
            "excel": "ExcelGeneratorNode",
            "pdf": "PDFGeneratorNode",
            "json": "JSONGeneratorNode",
            "word": "WordGeneratorNode"
        }
        
        node_type = format_map.get(output_format, "ExcelGeneratorNode")
        
        # Update output node
        if 'nodes' in config and 'generate_output' in config['nodes']:
            config['nodes']['generate_output']['node_type'] = node_type
        
        return config
    
    def _infer_operator(self, value: Any) -> str:
        """Infer operator from value type"""
        if isinstance(value, list):
            return "in"
        elif isinstance(value, str):
            if value.startswith('>'):
                return ">"
            elif value.startswith('<'):
                return "<"
            else:
                return "contains"
        else:
            return "="


# Singleton instance
_config_manager = None

def get_config_manager() -> ConfigurationManager:
    """Get singleton configuration manager"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager


def get_workflow_builder() -> WorkflowBuilder:
    """Get workflow builder"""
    return WorkflowBuilder(get_config_manager())