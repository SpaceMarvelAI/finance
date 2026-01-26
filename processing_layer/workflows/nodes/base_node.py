"""
Base Node Class - Pure Function Interface
All nodes must inherit from this and implement run()
"""

from typing import Dict, Any, List
from abc import ABC, abstractmethod
from datetime import datetime
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class BaseNode(ABC):
    """
    Base class for all nodes (tools)
    
    Nodes are PURE FUNCTIONS:
    - No decisions
    - No state
    - Same input = same output
    - Fast and cacheable
    """
    
    def __init__(self):
        self.node_type = self.__class__.__name__
        self.logger = logger
    
    @abstractmethod
    def run(self, input_data: Any, params: Dict[str, Any] = None) -> Any:
        """
        Execute node logic
        
        Args:
            input_data: Input from previous node or agent
            params: Configuration parameters
            
        Returns:
            Output for next node or agent
        """
        raise NotImplementedError(f"{self.node_type} must implement run()")
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get node metadata for registry
        
        Returns:
            Node definition with schema
        """
        return {
            "node_type": self.node_type,
            "name": getattr(self, 'name', self.node_type),
            "category": getattr(self, 'category', 'unknown'),
            "description": getattr(self, 'description', ''),
            "input_schema": getattr(self, 'input_schema', {}),
            "output_schema": getattr(self, 'output_schema', {}),
        }
    
    def _log_execution(self, input_size: int, output_size: int, duration_ms: float):
        """Log node execution metrics"""
        self.logger.info(
            f"{self.node_type} executed: "
            f"input={input_size}, output={output_size}, "
            f"duration={duration_ms:.2f}ms"
        )


class NodeRegistry:
    """
    Registry of all available nodes
    Used by frontend to show node library
    Used by agents to instantiate nodes
    """
    
    _nodes = {}
    
    @classmethod
    def register(cls, node_class):
        """Register a node class"""
        node_type = node_class.__name__
        cls._nodes[node_type] = node_class
        logger.info(f"Registered node: {node_type}")
        return node_class
    
    @classmethod
    def get_node(cls, node_type: str) -> BaseNode:
        """Get node instance by type"""
        if node_type not in cls._nodes:
            raise ValueError(f"Node not found: {node_type}")
        return cls._nodes[node_type]()
    
    @classmethod
    def get_all_nodes(cls) -> Dict[str, Any]:
        """Get all registered nodes"""
        return {
            node_type: node_class().get_metadata()
            for node_type, node_class in cls._nodes.items()
        }
    
    @classmethod
    def get_nodes_by_category(cls) -> Dict[str, List[Dict]]:
        """Get nodes grouped by category"""
        categories = {}
        for node_type, node_class in cls._nodes.items():
            node = node_class()
            metadata = node.get_metadata()
            category = metadata['category']
            
            if category not in categories:
                categories[category] = []
            
            categories[category].append(metadata)
        
        return categories


# Decorator to auto-register nodes
def register_node(node_class):
    """Decorator to automatically register node"""
    return NodeRegistry.register(node_class)