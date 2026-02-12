"""
Dynamic Agent
A configurable agent that can be created and modified at runtime
"""

from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime
from abc import ABC, abstractmethod
import asyncio

from ..core.base_agent import BaseAgent
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class DynamicAgent(BaseAgent):
    """
    Dynamic Agent
    
    A configurable agent that can be created and modified at runtime.
    Supports:
    - Dynamic capability loading
    - Runtime behavior modification
    - State persistence
    - Multi-step reasoning
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize dynamic agent
        
        Args:
            config: Agent configuration with capabilities and behavior
        """
        self.config = config
        self.agent_name = config.get('name', 'DynamicAgent')
        self.description = config.get('description', 'Dynamic agent')
        self.capabilities = config.get('capabilities', [])
        self.behavior_rules = config.get('behavior_rules', {})
        self.state = config.get('initial_state', {})
        self.execution_history = []
        
        # Initialize base agent
        super().__init__(self.agent_name)
        
        # Load capabilities
        self._load_capabilities()
        
        logger.info(f"Dynamic agent initialized: {self.agent_name}")
    
    def _load_capabilities(self):
        """Load agent capabilities from configuration"""
        for capability in self.capabilities:
            capability_type = capability.get('type')
            capability_config = capability.get('config', {})
            
            if capability_type == 'data_fetching':
                self._load_data_fetching_capability(capability_config)
            elif capability_type == 'calculation':
                self._load_calculation_capability(capability_config)
            elif capability_type == 'reporting':
                self._load_reporting_capability(capability_config)
            elif capability_type == 'analysis':
                self._load_analysis_capability(capability_config)
    
    def _load_data_fetching_capability(self, config: Dict[str, Any]):
        """Load data fetching capability"""
        # This would integrate with the existing node system
        logger.info(f"Loading data fetching capability for {self.agent_name}")
    
    def _load_calculation_capability(self, config: Dict[str, Any]):
        """Load calculation capability"""
        logger.info(f"Loading calculation capability for {self.agent_name}")
    
    def _load_reporting_capability(self, config: Dict[str, Any]):
        """Load reporting capability"""
        logger.info(f"Loading reporting capability for {self.agent_name}")
    
    def _load_analysis_capability(self, config: Dict[str, Any]):
        """Load analysis capability"""
        logger.info(f"Loading analysis capability for {self.agent_name}")
    
    async def execute(self, input_data: Any, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute dynamic agent logic
        
        Args:
            input_data: Input from user or previous agent
            params: Configuration parameters
            
        Returns:
            Agent output with results and metadata
        """
        params = params or {}
        
        try:
            # Log execution start
            self._log_decision(
                "Execute dynamic agent",
                f"Input type: {type(input_data)}, Params: {params}"
            )
            
            # Get execution plan
            execution_plan = self._create_execution_plan(input_data, params)
            
            # Execute plan step by step
            result = await self._execute_plan(execution_plan, input_data, params)
            
            # Return result with metadata
            return {
                'status': 'success',
                'agent_name': self.agent_name,
                'result': result,
                'execution_history': self.get_execution_history(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Dynamic agent execution failed: {str(e)}")
            return {
                'status': 'error',
                'agent_name': self.agent_name,
                'error': str(e),
                'execution_history': self.get_execution_history(),
                'timestamp': datetime.now().isoformat()
            }
    
    def _create_execution_plan(
        self, 
        input_data: Any, 
        params: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Create execution plan based on input and configuration
        
        Args:
            input_data: Input data
            params: Execution parameters
            
        Returns:
            List of execution steps
        """
        plan = []
        
        # Analyze input to determine required steps
        input_type = type(input_data).__name__
        
        # Get behavior rules for this input type
        behavior_rule = self.behavior_rules.get(input_type, {})
        
        # Build execution plan
        if behavior_rule.get('requires_data_fetching', False):
            plan.append({
                'step': 'data_fetching',
                'description': 'Fetch required data',
                'function': self._execute_data_fetching,
                'params': behavior_rule.get('data_fetching_params', {})
            })
        
        if behavior_rule.get('requires_calculation', False):
            plan.append({
                'step': 'calculation',
                'description': 'Perform calculations',
                'function': self._execute_calculation,
                'params': behavior_rule.get('calculation_params', {})
            })
        
        if behavior_rule.get('requires_analysis', False):
            plan.append({
                'step': 'analysis',
                'description': 'Analyze data',
                'function': self._execute_analysis,
                'params': behavior_rule.get('analysis_params', {})
            })
        
        if behavior_rule.get('requires_reporting', False):
            plan.append({
                'step': 'reporting',
                'description': 'Generate report',
                'function': self._execute_reporting,
                'params': behavior_rule.get('reporting_params', {})
            })
        
        return plan
    
    async def _execute_plan(
        self, 
        plan: List[Dict[str, Any]], 
        input_data: Any, 
        params: Dict[str, Any]
    ) -> Any:
        """
        Execute the execution plan
        
        Args:
            plan: Execution plan
            input_data: Input data
            params: Execution parameters
            
        Returns:
            Final result
        """
        current_data = input_data
        
        for step in plan:
            step_name = step['step']
            step_function = step['function']
            step_params = step['params']
            
            self._log_decision(
                f"Execute step: {step_name}",
                f"Function: {step_function.__name__}"
            )
            
            # Execute step
            if asyncio.iscoroutinefunction(step_function):
                result = await step_function(current_data, step_params)
            else:
                result = step_function(current_data, step_params)
            
            # Update current data
            current_data = result
            
            # Log step completion
            self._log_decision(
                f"Completed step: {step_name}",
                f"Result type: {type(result)}"
            )
        
        return current_data
    
    async def _execute_data_fetching(self, input_data: Any, params: Dict[str, Any]) -> Any:
        """Execute data fetching step"""
        # This would integrate with the existing node system
        self._log_decision("Data fetching", "Fetching required data")
        return input_data
    
    async def _execute_calculation(self, input_data: Any, params: Dict[str, Any]) -> Any:
        """Execute calculation step"""
        self._log_decision("Calculation", "Performing calculations")
        return input_data
    
    async def _execute_analysis(self, input_data: Any, params: Dict[str, Any]) -> Any:
        """Execute analysis step"""
        self._log_decision("Analysis", "Analyzing data")
        return input_data
    
    async def _execute_reporting(self, input_data: Any, params: Dict[str, Any]) -> Any:
        """Execute reporting step"""
        self._log_decision("Reporting", "Generating report")
        return input_data
    
    def update_capabilities(self, new_capabilities: List[Dict[str, Any]]):
        """Update agent capabilities"""
        self.capabilities.extend(new_capabilities)
        self._load_capabilities()
        logger.info(f"Updated capabilities for {self.agent_name}")
    
    def update_behavior_rules(self, new_rules: Dict[str, Any]):
        """Update agent behavior rules"""
        self.behavior_rules.update(new_rules)
        logger.info(f"Updated behavior rules for {self.agent_name}")
    
    def get_capabilities(self) -> List[Dict[str, Any]]:
        """Get agent capabilities"""
        return self.capabilities
    
    def get_state(self) -> Dict[str, Any]:
        """Get current agent state"""
        return self.state
    
    def update_state(self, new_state: Dict[str, Any]):
        """Update agent state"""
        self.state.update(new_state)
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get agent metadata"""
        return {
            'agent_name': self.agent_name,
            'description': self.description,
            'capabilities': self.capabilities,
            'behavior_rules': self.behavior_rules,
            'state': self.state,
            'execution_history': self.get_execution_history()
        }
    
    def reset(self):
        """Reset agent to initial state"""
        self.state = self.config.get('initial_state', {})
        self.execution_history = []
        logger.info(f"Reset agent: {self.agent_name}")
    
    def clone(self) -> 'DynamicAgent':
        """Create a clone of this agent"""
        return DynamicAgent(self.config.copy())
    
    def validate_config(self) -> List[str]:
        """
        Validate agent configuration
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required fields
        if not self.agent_name:
            errors.append("Agent name is required")
        
        if not self.capabilities:
            errors.append("Agent must have at least one capability")
        
        # Validate capabilities
        for i, capability in enumerate(self.capabilities):
            if 'type' not in capability:
                errors.append(f"Capability {i} missing type")
        
        return errors
    
    def optimize_for_report_type(self, report_type: str):
        """
        Optimize agent configuration for a specific report type
        
        Args:
            report_type: Type of report to optimize for
        """
        optimization_config = self._get_report_optimization_config(report_type)
        self.update_capabilities(optimization_config.get('capabilities', []))
        self.update_behavior_rules(optimization_config.get('behavior_rules', {}))
        
        logger.info(f"Optimized {self.agent_name} for {report_type}")
    
    def _get_report_optimization_config(self, report_type: str) -> Dict[str, Any]:
        """Get optimization configuration for a specific report type"""
        configs = {
            'ap_aging': {
                'capabilities': [
                    {
                        'type': 'data_fetching',
                        'config': {'required_data': ['invoices', 'payments']}
                    },
                    {
                        'type': 'calculation',
                        'config': {'calculations': ['outstanding', 'aging']}
                    },
                    {
                        'type': 'analysis',
                        'config': {'analysis_type': 'aging_bucket_analysis'}
                    }
                ],
                'behavior_rules': {
                    'dict': {
                        'requires_data_fetching': True,
                        'requires_calculation': True,
                        'requires_analysis': True,
                        'requires_reporting': True
                    }
                }
            },
            'ar_aging': {
                'capabilities': [
                    {
                        'type': 'data_fetching',
                        'config': {'required_data': ['sales_invoices', 'customer_payments']}
                    },
                    {
                        'type': 'calculation',
                        'config': {'calculations': ['outstanding', 'aging']}
                    },
                    {
                        'type': 'analysis',
                        'config': {'analysis_type': 'customer_aging_analysis'}
                    }
                ],
                'behavior_rules': {
                    'dict': {
                        'requires_data_fetching': True,
                        'requires_calculation': True,
                        'requires_analysis': True,
                        'requires_reporting': True
                    }
                }
            },
            'ap_register': {
                'capabilities': [
                    {
                        'type': 'data_fetching',
                        'config': {'required_data': ['invoices', 'payments']}
                    },
                    {
                        'type': 'calculation',
                        'config': {'calculations': ['outstanding']}
                    },
                    {
                        'type': 'reporting',
                        'config': {'report_type': 'register'}
                    }
                ],
                'behavior_rules': {
                    'dict': {
                        'requires_data_fetching': True,
                        'requires_calculation': True,
                        'requires_reporting': True
                    }
                }
            },
            'ar_register': {
                'capabilities': [
                    {
                        'type': 'data_fetching',
                        'config': {'required_data': ['sales_invoices', 'customer_payments']}
                    },
                    {
                        'type': 'calculation',
                        'config': {'calculations': ['outstanding']}
                    },
                    {
                        'type': 'reporting',
                        'config': {'report_type': 'register'}
                    }
                ],
                'behavior_rules': {
                    'dict': {
                        'requires_data_fetching': True,
                        'requires_calculation': True,
                        'requires_reporting': True
                    }
                }
            }
        }
        
        return configs.get(report_type, {
            'capabilities': [],
            'behavior_rules': {}
        })