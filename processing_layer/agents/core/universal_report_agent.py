"""
Universal Report Agent
Configuration-driven report generation
"""

from typing import Dict, Any
from processing_layer.agents.core.base_agent import BaseAgent, register_agent
from processing_layer.workflows.nodes import NodeRegistry
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


@register_agent
class UniversalReportAgent(BaseAgent):
    """
    Universal Report Agent - Configuration Driven
    
    Generates ANY report based on configuration
    No hardcoded logic
    
    Configuration Schema:
    {
        "report_type": "string",
        "pipeline": ["step1", "step2", ...],
        "nodes": {
            "step1": {
                "node_type": "NodeClassName",
                "params": {...}
            }
        }
    }
    """
    
    def __init__(self, report_config: Dict[str, Any]):
        """
        Initialize with configuration
        
        Args:
            report_config: Complete report configuration
        """
        report_type = report_config.get('report_type', 'universal')
        super().__init__(f"UniversalReportAgent_{report_type}")
        
        self.config = report_config
        self.pipeline = report_config.get('pipeline', [])
        self.node_configs = report_config.get('nodes', {})
        
    def execute(self, input_data: Any = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute report generation pipeline
        
        Args:
            input_data: Optional input data
            params: Runtime parameters (override config)
            
        Returns:
            {
                "status": "success|error",
                "report_type": "...",
                "data": {...},
                "execution_history": [...]
            }
        """
        params = params or {}
        
        # Merge config with runtime params
        runtime_config = {**self.config, **params}
        
        self._log_decision(
            "Starting configurable pipeline",
            f"Pipeline steps: {len(self.pipeline)}"
        )
        
        # Execute pipeline sequentially
        data = input_data
        
        for step in self.pipeline:
            try:
                data = self._execute_step(step, data, runtime_config)
                
                data_size = len(data) if isinstance(data, (list, dict)) else 'N/A'
                self._log_decision(
                    f"Completed step: {step}",
                    f"Output size: {data_size}"
                )
                
            except Exception as e:
                logger.error(f"Pipeline step '{step}' failed: {e}", exc_info=True)
                return {
                    'status': 'error',
                    'error': str(e),
                    'failed_step': step,
                    'execution_history': self.get_execution_history()
                }
        
        return {
            'status': 'success',
            'report_type': self.config.get('report_type'),
            'data': data,
            'execution_history': self.get_execution_history()
        }
    
    def _execute_step(self, step: str, data: Any, config: Dict[str, Any]) -> Any:
        """
        Execute a single pipeline step
        
        Args:
            step: Step name
            data: Current data
            config: Merged configuration
            
        Returns:
            Transformed data
        """
        # Get node configuration for this step
        step_config = self.node_configs.get(step, {})
        
        if not step_config:
            raise ValueError(f"No configuration found for step: {step}")
        
        node_type = step_config.get('node_type')
        node_params = step_config.get('params', {})
        
        # Merge with runtime overrides
        runtime_overrides = config.get(f'{step}_params', {})
        merged_params = {**node_params, **runtime_overrides}
        
        # Get node from registry
        try:
            node = NodeRegistry.get_node(node_type)
        except Exception as e:
            raise ValueError(f"Node type '{node_type}' not found: {e}")
        
        self._log_node_call(node_type, merged_params)
        
        # Execute node
        result = node.run(data, params=merged_params)
        
        return result