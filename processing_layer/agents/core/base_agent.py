"""
Base Agent Class - Decision Makers
All agents must inherit from this and implement execute()
"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    Base class for all agents (decision makers)
    
    Agents are INTELLIGENT:
    - Make decisions based on context
    - Choose which nodes to use
    - Determine execution order
    - Handle errors and retries
    - Can use LLM for intelligence
    """
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logger
        self.execution_history = []
    
    @abstractmethod
    def execute(self, input_data: Any, params: Dict[str, Any] = None) -> Any:
        """
        Execute agent logic
        
        Args:
            input_data: Input from user or previous agent
            params: Configuration parameters
            
        Returns:
            Agent output (could be data or file path)
        """
        raise NotImplementedError(f"{self.agent_name} must implement execute()")
    
    def _log_decision(self, decision: str, reason: str):
        """Log agent decisions for transparency"""
        self.logger.info(f"[{self.agent_name}] DECISION: {decision} | REASON: {reason}")
        self.execution_history.append({
            'decision': decision,
            'reason': reason,
            'timestamp': self._get_timestamp()
        })
    
    def _log_node_call(self, node_name: str, params: Dict = None):
        """Log when agent calls a node"""
        self.logger.info(f"[{self.agent_name}] CALLING NODE: {node_name} with params {params}")
    
    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_execution_history(self) -> list:
        """Get history of decisions made during execution"""
        return self.execution_history
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get agent metadata for registry
        
        Returns:
            Agent definition
        """
        return {
            "agent_name": self.agent_name,
            "agent_type": self.__class__.__name__,
            "description": getattr(self, 'description', ''),
            "capabilities": getattr(self, 'capabilities', []),
            "input_schema": getattr(self, 'input_schema', {}),
            "output_schema": getattr(self, 'output_schema', {}),
        }


class AgentRegistry:
    """
    Registry of all available agents
    Used by orchestrator to select agents
    """
    
    _agents = {}
    
    @classmethod
    def register(cls, agent_class):
        """Register an agent class"""
        agent_type = agent_class.__name__
        cls._agents[agent_type] = agent_class
        logger.info(f"Registered agent: {agent_type}")
        return agent_class
    
    @classmethod
    def get_agent(cls, agent_type: str, *args, **kwargs) -> BaseAgent:
        """Get agent instance by type"""
        if agent_type not in cls._agents:
            raise ValueError(f"Agent not found: {agent_type}")
        return cls._agents[agent_type](*args, **kwargs)
    
    @classmethod
    def get_all_agents(cls) -> Dict[str, Any]:
        """Get all registered agents"""
        return {
            agent_type: agent_class().get_metadata()
            for agent_type, agent_class in cls._agents.items()
        }
    
    @classmethod
    def get_agents_by_category(cls) -> Dict[str, list]:
        """Get agents grouped by category"""
        categories = {}
        for agent_type, agent_class in cls._agents.items():
            # Instantiate temporarily to get metadata
            agent = agent_class() if not agent_class.__init__.__code__.co_argcount > 1 else None
            if agent:
                category = getattr(agent, 'category', 'other')
                if category not in categories:
                    categories[category] = []
                categories[category].append(agent.get_metadata())
        
        return categories


# Decorator to auto-register agents
def register_agent(agent_class):
    """Decorator to automatically register agent"""
    return AgentRegistry.register(agent_class)