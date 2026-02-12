"""
LangGraph Workflow Builder
Builds and configures LangGraph workflows from specifications
"""

from typing import Dict, Any, List, Callable, Optional, Union, Annotated
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.prebuilt import ToolNode
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from typing_extensions import TypedDict

from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class WorkflowState(TypedDict, total=False):
    """Simplified workflow state without complex nested types"""
    query: str
    user_id: str
    company_id: str
    context: dict
    data: dict
    current_step: str
    execution_history: list
    error_state: dict


class WorkflowBuilder:
    """
    LangGraph workflow builder
    
    Provides a fluent API for building complex agent workflows
    with state management, conditional routing, and error handling
    """
    
    def __init__(self):
        # Initialize graph with simple TypedDict state
        self.graph = StateGraph(WorkflowState)
        self.nodes = {}
        self.edges = []
        self.conditional_edges = []
        
    def _get_state_schema(self) -> Dict[str, Any]:
        """Define the state schema for the workflow"""
        return WorkflowState
    
    def add_node(
        self, 
        node_name: str, 
        node_function: Callable,
        node_type: str = 'function',
        node_params: Optional[Dict[str, Any]] = None
    ) -> 'WorkflowBuilder':
        """
        Add a node to the workflow
        
        Args:
            node_name: Name of the node
            node_function: Function or agent to execute at this node
            node_type: Type of node (function, agent, tool)
            node_params: Configuration parameters for the node
            
        Returns:
            Self for chaining
        """
        # Wrap the node function to handle state properly
        wrapped_function = self._wrap_node_function(node_name, node_function, node_type, node_params or {})
        
        self.graph.add_node(node_name, wrapped_function)
        self.nodes[node_name] = {
            'function': node_function,
            'type': node_type,
            'wrapped': wrapped_function,
            'params': node_params or {}
        }
        
        logger.info(f"Added node: {node_name} (type: {node_type}) | Params: {node_params}")
        return self
    
    def add_edge(self, source: str, target: str) -> 'WorkflowBuilder':
        """
        Add a direct edge between nodes
        
        Args:
            source: Source node name
            target: Target node name
            
        Returns:
            Self for chaining
        """
        self.graph.add_edge(source, target)
        self.edges.append({'source': source, 'target': target})
        
        logger.info(f"Added edge: {source} -> {target}")
        return self
    
    def add_conditional_edges(
        self, 
        source: str, 
        condition: Callable,
        mapping: Optional[Dict[str, str]] = None
    ) -> 'WorkflowBuilder':
        """
        Add conditional edges based on node output
        
        Args:
            source: Source node name
            condition: Function that determines next node
            mapping: Optional mapping of condition results to node names
            
        Returns:
            Self for chaining
        """
        if mapping:
            self.graph.add_conditional_edges(source, condition, mapping)
        else:
            self.graph.add_conditional_edges(source, condition)
        
        self.conditional_edges.append({
            'source': source,
            'condition': condition,
            'mapping': mapping
        })
        
        logger.info(f"Added conditional edges from: {source}")
        return self
    
    def set_entry_point(self, node_name: str) -> 'WorkflowBuilder':
        """
        Set the entry point of the workflow
        
        Args:
            node_name: Name of the entry node
            
        Returns:
            Self for chaining
        """
        self.graph.set_entry_point(node_name)
        logger.info(f"Set entry point: {node_name}")
        return self
    
    def add_state_update(
        self, 
        node_name: str, 
        update_function: Callable
    ) -> 'WorkflowBuilder':
        """
        Add a state update function to a node
        
        Args:
            node_name: Name of the node
            update_function: Function to update state
            
        Returns:
            Self for chaining
        """
        if node_name in self.nodes:
            self.nodes[node_name]['state_update'] = update_function
            logger.info(f"Added state update to node: {node_name}")
        return self
    
    def add_error_handler(
        self, 
        node_name: str, 
        error_handler: Callable
    ) -> 'WorkflowBuilder':
        """
        Add an error handler to a node
        
        Args:
            node_name: Name of the node
            error_handler: Function to handle errors
            
        Returns:
            Self for chaining
        """
        if node_name in self.nodes:
            self.nodes[node_name]['error_handler'] = error_handler
            logger.info(f"Added error handler to node: {node_name}")
        return self
    
    def compile(
        self, 
        checkpointer: Optional[BaseCheckpointSaver] = None,
        interrupt_before: Optional[List[str]] = None,
        interrupt_after: Optional[List[str]] = None
    ) -> StateGraph:
        """
        Compile the workflow into a StateGraph
        
        Args:
            checkpointer: Checkpoint saver for persistence
            interrupt_before: List of nodes to interrupt before
            interrupt_after: List of nodes to interrupt after
            
        Returns:
            Compiled StateGraph
        """
        try:
            # Compile the graph into a runnable
            if interrupt_before:
                compiled = self.graph.compile(
                    checkpointer=checkpointer,
                    interrupt_before=interrupt_before
                )
            elif interrupt_after:
                compiled = self.graph.compile(
                    checkpointer=checkpointer,
                    interrupt_after=interrupt_after
                )
            else:
                compiled = self.graph.compile(checkpointer=checkpointer)
            
            logger.info("Workflow compiled successfully")
            return compiled
            
        except Exception as e:
            logger.error(f"Failed to compile workflow: {str(e)}")
            raise
    
    def _wrap_node_function(
        self, 
        node_name: str, 
        node_function: Callable,
        node_type: str,
        node_params: Dict[str, Any] = None
    ) -> Callable:
        """
        Wrap a node function to handle state and error management, with detailed logging.
        """
        node_params = node_params or {}
        
        def wrapped_node(state: Dict[str, Any]) -> Dict[str, Any]:
            try:
                # Initialize missing state fields
                if 'execution_history' not in state:
                    state['execution_history'] = []
                if 'error_state' not in state:
                    state['error_state'] = None
                if 'current_step' not in state:
                    state['current_step'] = node_name
                    
                state['current_step'] = node_name
                logger.info(f"[DEBUG] Executing node: {node_name} | Type: {node_type} | Input state type: {type(state)} | Keys: {list(state.keys())} | Node params: {node_params}")
                logger.info(f"[DEBUG] Input state value: {state}")
                
                # Execute the node function based on type
                if node_type == 'agent':
                    # Check if this is a workflow node (has .run(data, params) signature)
                    # vs an agent (has .execute(state) signature)
                    # For now, try calling with (data, params=), fall back to (state) if it fails
                    try:
                        input_data = state.get('data', state)
                        result = node_function(input_data, params=node_params)
                        logger.info(f"[DEBUG] Agent called with (data, params=...)")
                    except TypeError:
                        # Fall back to agent-style call
                        result = node_function(state)
                        logger.info(f"[DEBUG] Agent called with (state)")
                elif node_type == 'tool':
                    result = self._handle_tool_node(node_function, state)
                else:
                    # For function nodes, pass state['data'] or full state as first arg, and node_params as second arg
                    input_data = state.get('data', state)
                    result = node_function(input_data, params=node_params)
                
                logger.info(f"[DEBUG] Node {node_name} returned type: {type(result)} | Value: {result}")
                
                # Convert result to state update dict
                # LangGraph requires nodes to return dicts to update state
                if not isinstance(result, dict):
                    # If node returns non-dict (list, string, etc), wrap it in a data key
                    state_update = {'data': result}
                    logger.info(f"[DEBUG] Wrapped non-dict result in state_update: {state_update}")
                else:
                    state_update = result
                
                state['execution_history'].append({
                    'node': node_name,
                    'status': 'success',
                    'timestamp': self._get_timestamp(),
                    'result': str(result)[:500]  # Truncate for log safety
                })
                if node_name in self.nodes and 'state_update' in self.nodes[node_name]:
                    state_update_fn = self.nodes[node_name]['state_update']
                    state_update = state_update_fn(state, state_update)
                return state_update
            except Exception as e:
                logger.error(f"[DEBUG] Error in node {node_name}: {str(e)} | State: {state}")
                state['execution_history'].append({
                    'node': node_name,
                    'status': 'error',
                    'timestamp': self._get_timestamp(),
                    'error': str(e)
                })
                state['error_state'] = {
                    'node': node_name,
                    'error': str(e),
                    'timestamp': self._get_timestamp()
                }
                if node_name in self.nodes and 'error_handler' in self.nodes[node_name]:
                    error_handler = self.nodes[node_name]['error_handler']
                    return error_handler(state, e)
                raise
        return wrapped_node
    
    def _handle_tool_node(
        self, 
        tool_function: Callable,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle tool node execution
        
        Args:
            tool_function: Tool function to execute
            state: Current workflow state
            
        Returns:
            Updated state
        """
        # Get tool calls from state
        messages = state.get('messages', [])
        if not messages:
            return state
        
        # Execute tool calls
        tool_calls = []
        for message in messages:
            if hasattr(message, 'tool_calls'):
                tool_calls.extend(message.tool_calls)
        
        if not tool_calls:
            return state
        
        # Execute tools and collect results
        tool_results = []
        for tool_call in tool_calls:
            try:
                result = tool_function(tool_call)
                tool_results.append({
                    'tool_call_id': tool_call['id'],
                    'result': result
                })
            except Exception as e:
                logger.error(f"Tool execution failed: {str(e)}")
                tool_results.append({
                    'tool_call_id': tool_call['id'],
                    'error': str(e)
                })
        
        # Add tool results to messages
        state['messages'].extend([
            AIMessage(content=f"Tool result: {result}")
            for result in tool_results
        ])
        
        return state
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_workflow_spec(self) -> Dict[str, Any]:
        """Get the workflow specification"""
        return {
            'nodes': self.nodes,
            'edges': self.edges,
            'conditional_edges': self.conditional_edges,
            'entry_point': getattr(self.graph, 'entry_point', None)
        }
    
    def validate_workflow(self) -> List[str]:
        """
        Validate the workflow configuration
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check if entry point exists
        entry_point = getattr(self.graph, 'entry_point', None)
        if entry_point and entry_point not in self.nodes:
            errors.append(f"Entry point '{entry_point}' does not exist")
        
        # Check if all edge targets exist
        for edge in self.edges:
            if edge['target'] not in self.nodes:
                errors.append(f"Edge target '{edge['target']}' does not exist")
        
        # Check for cycles (basic check)
        # This is a simplified cycle detection
        visited = set()
        for node in self.nodes:
            if self._has_cycle(node, visited, set()):
                errors.append(f"Cycle detected starting from node '{node}'")
        
        return errors
    
    def _has_cycle(
        self, 
        node: str, 
        visited: set, 
        path: set
    ) -> bool:
        """
        Check if there's a cycle starting from the given node
        
        Args:
            node: Node to check
            visited: Set of already visited nodes
            path: Set of nodes in current path
            
        Returns:
            True if cycle detected
        """
        if node in path:
            return True
        
        if node in visited:
            return False
        
        visited.add(node)
        path.add(node)
        
        # Check all outgoing edges
        for edge in self.edges:
            if edge['source'] == node:
                if self._has_cycle(edge['target'], visited, path):
                    return True
        
        path.remove(node)
        return False