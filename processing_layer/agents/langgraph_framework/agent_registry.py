"""
LangGraph Agent Registry
Registry for managing and discovering LangGraph-based agents
"""

from typing import Dict, Any, List, Optional, Type, Callable
from datetime import datetime
import asyncio
from abc import ABC, abstractmethod

from ..core.base_agent import BaseAgent
from .dynamic_agent import DynamicAgent
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class LangGraphAgentRegistry:
    """
    LangGraph Agent Registry
    
    Manages registration, discovery, and lifecycle of LangGraph agents.
    Supports both static and dynamic agent registration.
    """
    
    def __init__(self):
        self.agents = {}  # agent_type -> agent_class/instance
        self.agent_instances = {}  # agent_id -> agent_instance
        self.agent_metadata = {}  # agent_type -> metadata
        self.capabilities_index = {}  # capability -> list of agent types
        
        # Register built-in report nodes
        self._register_builtin_nodes()
    
    def _register_builtin_nodes(self):
        """Register built-in report nodes"""
        try:
            from processing_layer.workflows.nodes.output_nodes.report_templates.ap_aging_node_fixed import APAgingReportNode
            self.register_agent(
                'APAgingReportNode',
                APAgingReportNode,
                {
                    'capabilities': ['reporting', 'excel_generation'],
                    'description': 'AP Aging Report Node'
                }
            )
            logger.info("Registered APAgingReportNode")
        except ImportError as e:
            logger.warning(f"Could not register APAgingReportNode: {e}")
        
    def register_agent(
        self, 
        agent_type: str, 
        agent_class: Type[BaseAgent],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Register a static agent class
        
        Args:
            agent_type: Type identifier for the agent
            agent_class: Agent class to register
            metadata: Optional metadata about the agent
        """
        self.agents[agent_type] = agent_class
        self.agent_metadata[agent_type] = metadata or {}
        
        # Index capabilities
        if metadata and 'capabilities' in metadata:
            for capability in metadata['capabilities']:
                if capability not in self.capabilities_index:
                    self.capabilities_index[capability] = []
                self.capabilities_index[capability].append(agent_type)
        
        logger.info(f"Registered agent: {agent_type}")
    
    def register_dynamic_agent(
        self, 
        agent_config: Dict[str, Any]
    ) -> str:
        """
        Register a dynamic agent
        
        Args:
            agent_config: Configuration for the dynamic agent
            
        Returns:
            Agent ID
        """
        agent = DynamicAgent(agent_config)
        agent_id = f"dynamic_{agent.agent_name}_{datetime.now().timestamp()}"
        
        self.agent_instances[agent_id] = agent
        
        # Index capabilities
        for capability in agent.capabilities:
            capability_type = capability.get('type')
            if capability_type not in self.capabilities_index:
                self.capabilities_index[capability_type] = []
            self.capabilities_index[capability_type].append(agent_id)
        
        logger.info(f"Registered dynamic agent: {agent_id}")
        return agent_id
    
    def get_agent(
        self, 
        agent_type: str, 
        agent_id: Optional[str] = None,
        **kwargs
    ) -> BaseAgent:
        """
        Get an agent instance
        
        Args:
            agent_type: Type of agent to get
            agent_id: Specific agent ID (for dynamic agents)
            **kwargs: Additional arguments for agent initialization
            
        Returns:
            Agent instance
        """
        if agent_id and agent_id in self.agent_instances:
            return self.agent_instances[agent_id]
        
        if agent_type in self.agents:
            agent_class = self.agents[agent_type]
            return agent_class(**kwargs)
        
        raise ValueError(f"Agent not found: {agent_type}")
    
    def get_dynamic_agent(self, agent_id: str) -> DynamicAgent:
        """
        Get a dynamic agent instance
        
        Args:
            agent_id: ID of the dynamic agent
            
        Returns:
            DynamicAgent instance
        """
        if agent_id not in self.agent_instances:
            raise ValueError(f"Dynamic agent not found: {agent_id}")
        
        return self.agent_instances[agent_id]
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """
        List all registered agents
        
        Returns:
            List of agent metadata
        """
        agents = []
        
        # Static agents
        for agent_type, agent_class in self.agents.items():
            metadata = self.agent_metadata.get(agent_type, {})
            agents.append({
                'type': agent_type,
                'class': agent_class.__name__,
                'metadata': metadata,
                'dynamic': False
            })
        
        # Dynamic agents
        for agent_id, agent_instance in self.agent_instances.items():
            agents.append({
                'id': agent_id,
                'type': 'dynamic',
                'class': agent_instance.__class__.__name__,
                'metadata': agent_instance.get_metadata(),
                'dynamic': True
            })
        
        return agents
    
    def find_agents_by_capability(self, capability: str) -> List[str]:
        """
        Find agents that support a specific capability
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of agent types/IDs
        """
        return self.capabilities_index.get(capability, [])
    
    def find_agents_by_capabilities(self, capabilities: List[str]) -> List[str]:
        """
        Find agents that support all specified capabilities
        
        Args:
            capabilities: List of capabilities to search for
            
        Returns:
            List of agent types/IDs
        """
        if not capabilities:
            return []
        
        # Start with agents that have the first capability
        result = set(self.find_agents_by_capability(capabilities[0]))
        
        # Intersect with agents that have other capabilities
        for capability in capabilities[1:]:
            result = result.intersection(set(self.find_agents_by_capability(capability)))
        
        return list(result)
    
    def get_agent_capabilities(self, agent_type: str) -> Dict[str, Any]:
        """
        Get capabilities of a specific agent type
        
        Args:
            agent_type: Type of agent
            
        Returns:
            Agent capabilities
        """
        if agent_type in self.agent_metadata:
            return self.agent_metadata[agent_type].get('capabilities', [])
        
        if agent_type in self.agents:
            # Create instance to get capabilities
            agent = self.agents[agent_type]()
            return agent.get_metadata().get('capabilities', [])
        
        return []
    
    def get_all_capabilities(self) -> List[str]:
        """Get all available capabilities"""
        return list(self.capabilities_index.keys())
    
    def update_agent_metadata(
        self, 
        agent_type: str, 
        metadata: Dict[str, Any]
    ):
        """
        Update agent metadata
        
        Args:
            agent_type: Type of agent
            metadata: New metadata
        """
        if agent_type in self.agent_metadata:
            self.agent_metadata[agent_type].update(metadata)
            logger.info(f"Updated metadata for agent: {agent_type}")
    
    def remove_agent(self, agent_type: str):
        """
        Remove a static agent
        
        Args:
            agent_type: Type of agent to remove
        """
        if agent_type in self.agents:
            del self.agents[agent_type]
            del self.agent_metadata[agent_type]
            
            # Remove from capabilities index
            for capability, agents in self.capabilities_index.items():
                if agent_type in agents:
                    agents.remove(agent_type)
            
            logger.info(f"Removed agent: {agent_type}")
    
    def remove_dynamic_agent(self, agent_id: str):
        """
        Remove a dynamic agent
        
        Args:
            agent_id: ID of dynamic agent to remove
        """
        if agent_id in self.agent_instances:
            agent = self.agent_instances[agent_id]
            
            # Remove from capabilities index
            for capability in agent.capabilities:
                capability_type = capability.get('type')
                if capability_type in self.capabilities_index:
                    if agent_id in self.capabilities_index[capability_type]:
                        self.capabilities_index[capability_type].remove(agent_id)
            
            del self.agent_instances[agent_id]
            logger.info(f"Removed dynamic agent: {agent_id}")
    
    def create_optimized_agent(
        self, 
        report_type: str, 
        user_id: str,
        optimization_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create an optimized dynamic agent for a specific report type
        
        Args:
            report_type: Type of report to optimize for
            user_id: User identifier
            optimization_params: Additional optimization parameters
            
        Returns:
            Agent ID
        """
        # Get base configuration for the report type
        base_config = self._get_report_agent_config(report_type, user_id)
        
        # Apply optimization parameters
        if optimization_params:
            base_config.update(optimization_params)
        
        # Create dynamic agent
        agent_id = self.register_dynamic_agent(base_config)
        
        # Optimize the agent for the report type
        agent = self.get_dynamic_agent(agent_id)
        agent.optimize_for_report_type(report_type)
        
        logger.info(f"Created optimized agent for {report_type}: {agent_id}")
        return agent_id
    
    def _get_report_agent_config(self, report_type: str, user_id: str) -> Dict[str, Any]:
        """Get base configuration for a report agent"""
        configs = {
            'ap_aging': {
                'name': f'APAgingAgent_{user_id}',
                'description': 'AP Aging analysis agent',
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
                    },
                    {
                        'type': 'reporting',
                        'config': {'report_type': 'ap_aging'}
                    }
                ],
                'behavior_rules': {
                    'dict': {
                        'requires_data_fetching': True,
                        'requires_calculation': True,
                        'requires_analysis': True,
                        'requires_reporting': True
                    }
                },
                'initial_state': {
                    'user_id': user_id,
                    'report_type': report_type,
                    'execution_count': 0
                }
            },
            'ar_aging': {
                'name': f'ARAgingAgent_{user_id}',
                'description': 'AR Aging analysis agent',
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
                    },
                    {
                        'type': 'reporting',
                        'config': {'report_type': 'ar_aging'}
                    }
                ],
                'behavior_rules': {
                    'dict': {
                        'requires_data_fetching': True,
                        'requires_calculation': True,
                        'requires_analysis': True,
                        'requires_reporting': True
                    }
                },
                'initial_state': {
                    'user_id': user_id,
                    'report_type': report_type,
                    'execution_count': 0
                }
            },
            'ap_register': {
                'name': f'APRegisterAgent_{user_id}',
                'description': 'AP Register agent',
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
                        'config': {'report_type': 'ap_register'}
                    }
                ],
                'behavior_rules': {
                    'dict': {
                        'requires_data_fetching': True,
                        'requires_calculation': True,
                        'requires_reporting': True
                    }
                },
                'initial_state': {
                    'user_id': user_id,
                    'report_type': report_type,
                    'execution_count': 0
                }
            },
            'ar_register': {
                'name': f'ARRegisterAgent_{user_id}',
                'description': 'AR Register agent',
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
                        'config': {'report_type': 'ar_register'}
                    }
                ],
                'behavior_rules': {
                    'dict': {
                        'requires_data_fetching': True,
                        'requires_calculation': True,
                        'requires_reporting': True
                    }
                },
                'initial_state': {
                    'user_id': user_id,
                    'report_type': report_type,
                    'execution_count': 0
                }
            }
        }
        
        return configs.get(report_type, {
            'name': f'GenericAgent_{user_id}',
            'description': 'Generic agent',
            'capabilities': [],
            'behavior_rules': {},
            'initial_state': {
                'user_id': user_id,
                'report_type': report_type,
                'execution_count': 0
            }
        })
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        return {
            'total_agents': len(self.agents) + len(self.agent_instances),
            'static_agents': len(self.agents),
            'dynamic_agents': len(self.agent_instances),
            'total_capabilities': len(self.capabilities_index),
            'capabilities': list(self.capabilities_index.keys()),
            'agent_types': list(self.agents.keys()),
            'dynamic_agent_ids': list(self.agent_instances.keys())
        }
    
    def validate_registry(self) -> List[str]:
        """
        Validate the registry state
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check for duplicate agent types
        agent_types = set(self.agents.keys())
        dynamic_agent_types = {agent.agent_name for agent in self.agent_instances.values()}
        duplicates = agent_types.intersection(dynamic_agent_types)
        if duplicates:
            errors.append(f"Duplicate agent types: {duplicates}")
        
        # Check for orphaned capabilities
        all_capabilities = set()
        for agent_type, metadata in self.agent_metadata.items():
            if 'capabilities' in metadata:
                all_capabilities.update(metadata['capabilities'])
        
        for agent_instance in self.agent_instances.values():
            all_capabilities.update([cap['type'] for cap in agent_instance.capabilities])
        
        orphaned_capabilities = all_capabilities - set(self.capabilities_index.keys())
        if orphaned_capabilities:
            errors.append(f"Orphaned capabilities: {orphaned_capabilities}")
        
        return errors
    
    def cleanup(self):
        """Clean up the registry"""
        self.agents.clear()
        self.agent_instances.clear()
        self.agent_metadata.clear()
        self.capabilities_index.clear()
        logger.info("Registry cleaned up")