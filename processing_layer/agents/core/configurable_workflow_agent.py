"""
Configurable Workflow Agent
Executes visual workflows from frontend
"""

from typing import Dict, Any, List, Optional
from collections import deque, defaultdict
from processing_layer.agents.core.base_agent import BaseAgent, register_agent
from processing_layer.workflows.nodes import NodeRegistry
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


@register_agent
class ConfigurableWorkflowAgent(BaseAgent):
    """
    Configurable Workflow Agent
    
    Executes workflows built visually in frontend
    Supports DAG execution with dependencies
    
    Workflow Schema:
    {
        "id": "workflow_id",
        "nodes": [
            {
                "id": "node_1",
                "type": "NodeClassName",
                "params": {...},
                "position": {"x": 100, "y": 100}
            }
        ],
        "edges": [
            {"source": "node_1", "target": "node_2"}
        ]
    }
    """
    
    def __init__(self, workflow_config: Optional[Dict] = None):
        """
        Initialize workflow agent
        
        Args:
            workflow_config: Optional default workflow configuration
        """
        super().__init__("ConfigurableWorkflowAgent")
        self.workflow_config = workflow_config or {}
    
    def execute(self, input_data: Any = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute workflow
        
        Args:
            input_data: Optional input data
            params: Runtime parameters including workflow_config
            
        Returns:
            {
                "status": "success|error",
                "workflow_id": "...",
                "result": {...},
                "node_outputs": {...}
            }
        """
        params = params or {}
        
        # Get workflow config (from params or instance)
        workflow_config = params.get('workflow_config', self.workflow_config)
        
        if not workflow_config:
            return {
                'status': 'error',
                'error': 'No workflow configuration provided'
            }
        
        # Extract workflow definition
        nodes = workflow_config.get('nodes', [])
        edges = workflow_config.get('edges', [])
        
        if not nodes:
            return {
                'status': 'error',
                'error': 'Workflow has no nodes'
            }
        
        self._log_decision(
            "Executing configurable workflow",
            f"Nodes: {len(nodes)}, Edges: {len(edges)}"
        )
        
        try:
            # Build execution order (topological sort)
            execution_order = self._topological_sort(nodes, edges)
            
            self._log_decision(
                "Execution order determined",
                f"Order: {execution_order}"
            )
            
            # Execute nodes in order
            node_outputs = {}
            
            for node_id in execution_order:
                # Get node definition
                node_def = next((n for n in nodes if n['id'] == node_id), None)
                
                if not node_def:
                    raise ValueError(f"Node {node_id} not found in definitions")
                
                # Get input data for this node
                input_for_node = self._get_node_input(node_id, edges, node_outputs, input_data)
                
                # Execute node
                result = self._execute_node(node_def, input_for_node, params)
                
                # Store output
                node_outputs[node_id] = result
                
                self._log_decision(
                    f"Completed node: {node_id}",
                    f"Type: {node_def['type']}"
                )
            
            # Get final output (last node in execution order)
            final_output = node_outputs.get(execution_order[-1])
            
            return {
                'status': 'success',
                'workflow_id': workflow_config.get('id'),
                'result': final_output,
                'node_outputs': node_outputs,
                'execution_history': self.get_execution_history()
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'workflow_id': workflow_config.get('id'),
                'execution_history': self.get_execution_history()
            }
    
    def _topological_sort(self, nodes: List[Dict], edges: List[Dict]) -> List[str]:
        """
        Topological sort for DAG execution order
        
        Args:
            nodes: List of node definitions
            edges: List of edge definitions
            
        Returns:
            Ordered list of node IDs
        """
        # Build adjacency list and in-degree
        adj = defaultdict(list)
        in_degree = defaultdict(int)
        
        # Initialize all nodes with 0 in-degree
        for node in nodes:
            in_degree[node['id']] = 0
        
        # Build graph
        for edge in edges:
            source = edge['source']
            target = edge['target']
            adj[source].append(target)
            in_degree[target] += 1
        
        # Find nodes with no dependencies (in-degree = 0)
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        
        if not queue:
            raise ValueError("Workflow has circular dependencies or no starting nodes")
        
        result = []
        
        while queue:
            node_id = queue.popleft()
            result.append(node_id)
            
            # Reduce in-degree for neighbors
            for neighbor in adj[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check if all nodes were processed
        if len(result) != len(nodes):
            raise ValueError("Workflow has circular dependencies")
        
        return result
    
    def _get_node_input(self, node_id: str, edges: List[Dict], outputs: Dict, initial_input: Any = None) -> Any:
        """
        Get input data for node from previous nodes
        
        Args:
            node_id: Current node ID
            edges: Edge definitions
            outputs: Previous node outputs
            initial_input: Initial workflow input
            
        Returns:
            Input data for node
        """
        # Find edges pointing to this node
        incoming = [e for e in edges if e['target'] == node_id]
        
        # If no incoming edges, use initial input
        if not incoming:
            return initial_input
        
        # If single input, return directly
        if len(incoming) == 1:
            source = incoming[0]['source']
            return outputs.get(source)
        
        # If multiple inputs, return as dict
        return {
            e['source']: outputs.get(e['source'])
            for e in incoming
        }
    
    def _execute_node(self, node_def: Dict, input_data: Any, params: Dict) -> Any:
        """
        Execute a single node
        
        Args:
            node_def: Node definition
            input_data: Input data
            params: Runtime parameters
            
        Returns:
            Node output
        """
        node_type = node_def['type']
        node_id = node_def['id']
        
        # Merge node params with runtime overrides
        node_params = node_def.get('params', {})
        runtime_overrides = params.get('node_overrides', {}).get(node_id, {})
        merged_params = {**node_params, **runtime_overrides}
        
        # Get node from registry
        try:
            node = NodeRegistry.get_node(node_type)
        except Exception as e:
            raise ValueError(f"Node type '{node_type}' not found: {e}")
        
        self._log_node_call(node_type, merged_params)
        
        # Execute
        return node.run(input_data, params=merged_params)