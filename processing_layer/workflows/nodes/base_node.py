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
    Enhanced for LangGraph integration with comprehensive schemas
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
    
    @classmethod
    def get_all_schemas(cls) -> Dict[str, Dict]:
        """
        Get comprehensive schemas for all nodes - CRITICAL for LangGraph
        Returns detailed information for LLM to understand and select nodes
        """
        schemas = {}
        for node_type, node_class in cls._nodes.items():
            try:
                node = node_class()
                metadata = node.get_metadata()
                
                # Enhanced schema with LangGraph-specific information
                schemas[node_type] = {
                    "name": node_type,
                    "description": metadata.get('description', ''),
                    "category": metadata.get('category', 'unknown'),
                    "input_schema": getattr(node, 'input_schema', {}),
                    "output_schema": getattr(node, 'output_schema', {}),
                    "allowed_parameters": getattr(node, 'ALLOWED_PARAMS', []),
                    "node_type": "function",  # For LangGraph compatibility
                    "pure_function": True,    # Indicates no side effects
                    "stateless": True,        # No internal state
                    "cacheable": True,        # Results can be cached
                    "metadata": metadata
                }
            except Exception as e:
                logger.error(f"Failed to get schema for node {node_type}: {e}")
                continue
        
        logger.info(f"Generated schemas for {len(schemas)} nodes for LangGraph")
        return schemas
    
    @classmethod
    def get_node_schema(cls, node_type: str) -> Dict:
        """
        Get schema for a specific node - for LLM node selection
        """
        if node_type not in cls._nodes:
            raise ValueError(f"Node not found: {node_type}")
        
        node = cls._nodes[node_type]()
        metadata = node.get_metadata()
        
        return {
            "name": node_type,
            "description": metadata.get('description', ''),
            "category": metadata.get('category', 'unknown'),
            "input_schema": getattr(node, 'input_schema', {}),
            "output_schema": getattr(node, 'output_schema', {}),
            "allowed_parameters": getattr(node, 'ALLOWED_PARAMS', []),
            "node_type": "function",
            "pure_function": True,
            "stateless": True,
            "cacheable": True,
            "metadata": metadata
        }
    
    @classmethod
    def get_nodes_by_functionality(cls, functionality: str) -> List[Dict]:
        """
        Get nodes by functionality keywords - for intelligent node discovery
        """
        functionality_keywords = {
            'data_fetch': ['fetch', 'get', 'retrieve', 'query'],
            'calculation': ['calculate', 'compute', 'process', 'transform'],
            'aggregation': ['group', 'filter', 'sort', 'aggregate', 'summarize'],
            'output': ['generate', 'create', 'export', 'output', 'report'],
            'analysis': ['analyze', 'detect', 'check', 'validate']
        }
        
        keywords = functionality_keywords.get(functionality.lower(), [functionality.lower()])
        matching_nodes = []
        
        for node_type, node_class in cls._nodes.items():
            node = node_class()
            metadata = node.get_metadata()
            description = metadata.get('description', '').lower()
            
            if any(keyword in description for keyword in keywords):
                matching_nodes.append({
                    'node_type': node_type,
                    'metadata': metadata,
                    'schema': cls.get_node_schema(node_type)
                })
        
        return matching_nodes
    
    @classmethod
    def validate_node_compatibility(cls, source_node: str, target_node: str) -> bool:
        """
        Validate if output of source node is compatible with input of target node
        Critical for LangGraph workflow validation
        """
        try:
            source_schema = cls.get_node_schema(source_node)
            target_schema = cls.get_node_schema(target_node)
            
            source_output = source_schema.get('output_schema', {})
            target_input = target_schema.get('input_schema', {})
            
            # Basic compatibility check - target input should accept source output
            if not source_output or not target_input:
                return True  # Can't validate, assume compatible
            
            # Check if target can accept the source output type
            source_output_type = source_output.get('type', 'object')
            target_input_type = target_input.get('type', 'object')
            
            return source_output_type == target_input_type or target_input_type == 'any'
            
        except Exception as e:
            logger.warning(f"Could not validate compatibility between {source_node} and {target_node}: {e}")
            return True  # Default to compatible if validation fails


# Decorator to auto-register nodes
def register_node(node_class):
    """Decorator to automatically register node"""
    return NodeRegistry.register(node_class)