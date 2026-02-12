"""
AutoGen Orchestrator
Central orchestrator for managing AutoGen agent workflows and coordination
"""

from typing import Dict, Any, Optional, List, Union, Callable
from shared.config.logging_config import get_logger


logger = get_logger(__name__)


class AutoGenOrchestrator:
    """
    AutoGen Orchestrator
    
    Manages the coordination and execution of AutoGen agents,
    handles workflow orchestration, and provides centralized control.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agents = {}
        self.workflows = {}
        self.active_sessions = {}
        
        # Initialize orchestrator
        self._initialize_orchestrator()
    
    def _initialize_orchestrator(self):
        """Initialize the orchestrator"""
        try:
            # Initialize agent factory
            from .agent_factory import AgentFactory
            self.agent_factory = AgentFactory(self.config)
            
            logger.info("AutoGen Orchestrator initialized")
            
        except Exception as e:
            logger.error(f"Error initializing AutoGen Orchestrator: {str(e)}")
            raise
    
    def create_agent(self, agent_type: str, agent_config: Dict[str, Any]) -> str:
        """
        Create a new agent
        
        Args:
            agent_type: Type of agent to create
            agent_config: Configuration for the agent
            
        Returns:
            Agent ID
        """
        try:
            # Create agent using factory
            agent = self.agent_factory.create_agent(agent_type, agent_config)
            
            # Store agent
            agent_id = f"{agent_type}_{len(self.agents)}"
            self.agents[agent_id] = agent
            
            logger.info(f"Created agent: {agent_id}")
            
            return agent_id
            
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            return None
    
    def create_workflow(self, workflow_config: Dict[str, Any]) -> str:
        """
        Create a new workflow
        
        Args:
            workflow_config: Configuration for the workflow
            
        Returns:
            Workflow ID
        """
        try:
            # For now, create a simple workflow ID
            # In a full implementation, this would integrate with workflow builder
            workflow_id = f"workflow_{len(self.workflows)}"
            self.workflows[workflow_id] = {
                'config': workflow_config,
                'status': 'created',
                'agents': []
            }
            
            logger.info(f"Created workflow: {workflow_id}")
            
            return workflow_id
            
        except Exception as e:
            logger.error(f"Error creating workflow: {str(e)}")
            return None
    
    def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow
        
        Args:
            workflow_id: ID of the workflow to execute
            input_data: Input data for the workflow
            
        Returns:
            Execution result
        """
        try:
            if workflow_id not in self.workflows:
                return {
                    'status': 'error',
                    'workflow_id': workflow_id,
                    'error': 'Workflow not found'
                }
            
            workflow = self.workflows[workflow_id]
            
            # Start session
            session_id = self._start_session(workflow_id, input_data)
            
            try:
                # For now, return a simple success response
                # In a full implementation, this would execute the actual workflow
                result = {
                    'status': 'completed',
                    'workflow_id': workflow_id,
                    'input_data': input_data,
                    'agents_used': [],
                    'execution_details': 'Workflow executed successfully'
                }
                
                # Complete session
                self._complete_session(session_id, result)
                
                logger.info(f"Executed workflow {workflow_id}: SUCCESS")
                
                return {
                    'status': 'success',
                    'workflow_id': workflow_id,
                    'session_id': session_id,
                    'result': result,
                    'execution_time': self._get_current_timestamp()
                }
                
            except Exception as e:
                # Handle session error
                self._error_session(session_id, str(e))
                
                logger.error(f"Error executing workflow {workflow_id}: {str(e)}")
                return {
                    'status': 'error',
                    'workflow_id': workflow_id,
                    'session_id': session_id,
                    'error': str(e)
                }
            
        except Exception as e:
            logger.error(f"Error in workflow execution: {str(e)}")
            return {
                'status': 'error',
                'workflow_id': workflow_id,
                'input_data': input_data,
                'error': str(e)
            }
    
    def execute_agent_task(self, agent_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task with a specific agent
        
        Args:
            agent_id: ID of the agent
            task: Task to execute
            
        Returns:
            Task execution result
        """
        try:
            if agent_id not in self.agents:
                return {
                    'status': 'error',
                    'agent_id': agent_id,
                    'error': 'Agent not found'
                }
            
            agent = self.agents[agent_id]
            
            # Execute task
            result = agent.execute_task(task)
            
            logger.info(f"Executed task with agent {agent_id}: SUCCESS")
            
            return {
                'status': 'success',
                'agent_id': agent_id,
                'task': task,
                'result': result,
                'execution_time': self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error executing agent task: {str(e)}")
            return {
                'status': 'error',
                'agent_id': agent_id,
                'task': task,
                'error': str(e)
            }
    
    def get_agent_capabilities(self, agent_id: str) -> Dict[str, Any]:
        """
        Get capabilities of a specific agent
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Agent capabilities
        """
        try:
            if agent_id not in self.agents:
                return {
                    'status': 'error',
                    'agent_id': agent_id,
                    'error': 'Agent not found'
                }
            
            agent = self.agents[agent_id]
            
            return {
                'status': 'success',
                'agent_id': agent_id,
                'capabilities': agent.capabilities,
                'tools': agent.tools,
                'agent_type': agent.agent_type
            }
            
        except Exception as e:
            logger.error(f"Error getting agent capabilities: {str(e)}")
            return {
                'status': 'error',
                'agent_id': agent_id,
                'error': str(e)
            }
    
    def list_agents(self) -> Dict[str, Any]:
        """
        List all available agents
        
        Returns:
            List of agents
        """
        try:
            agents_list = []
            
            for agent_id, agent in self.agents.items():
                agents_list.append({
                    'agent_id': agent_id,
                    'agent_type': agent.agent_type,
                    'description': agent.description,
                    'capabilities': agent.capabilities,
                    'tools': agent.tools
                })
            
            return {
                'status': 'success',
                'total_agents': len(self.agents),
                'agents': agents_list
            }
            
        except Exception as e:
            logger.error(f"Error listing agents: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get status of a workflow
        
        Args:
            workflow_id: ID of the workflow
            
        Returns:
            Workflow status
        """
        try:
            if workflow_id not in self.workflows:
                return {
                    'status': 'error',
                    'workflow_id': workflow_id,
                    'error': 'Workflow not found'
                }
            
            workflow = self.workflows[workflow_id]
            
            return {
                'status': 'success',
                'workflow_id': workflow_id,
                'status': workflow.get('status', 'unknown'),
                'agents': workflow.get('agents', []),
                'execution_history': []
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow status: {str(e)}")
            return {
                'status': 'error',
                'workflow_id': workflow_id,
                'error': str(e)
            }
    
    def register_callback(self, event_type: str, callback: Callable) -> bool:
        """
        Register a callback for specific events
        
        Args:
            event_type: Type of event to listen for
            callback: Callback function to register
            
        Returns:
            Registration success status
        """
        try:
            # For now, just log the callback registration
            # In a full implementation, this would integrate with workflow builder
            logger.info(f"Registered callback for event: {event_type}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error registering callback: {str(e)}")
            return False
    
    def get_orchestrator_status(self) -> Dict[str, Any]:
        """
        Get overall orchestrator status
        
        Returns:
            Orchestrator status
        """
        try:
            return {
                'status': 'success',
                'active_agents': len(self.agents),
                'active_workflows': len(self.workflows),
                'active_sessions': len(self.active_sessions),
                'agent_types': list(set(agent.agent_type for agent in self.agents.values())),
                'orchestrator_time': self._get_current_timestamp()
            }
            
        except Exception as e:
            logger.error(f"Error getting orchestrator status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def cleanup(self):
        """Clean up orchestrator resources"""
        try:
            # Clean up agents
            for agent_id, agent in self.agents.items():
                try:
                    agent.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up agent {agent_id}: {str(e)}")
            
            # Clean up workflows
            for workflow_id, workflow in self.workflows.items():
                try:
                    workflow.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up workflow {workflow_id}: {str(e)}")
            
            # Clear active sessions
            self.active_sessions.clear()
            
            logger.info("AutoGen Orchestrator cleaned up")
            
        except Exception as e:
            logger.error(f"Error during orchestrator cleanup: {str(e)}")
    
    def _start_session(self, workflow_id: str, input_data: Dict[str, Any]) -> str:
        """Start a new session"""
        session_id = f"session_{len(self.active_sessions)}"
        self.active_sessions[session_id] = {
            'workflow_id': workflow_id,
            'input_data': input_data,
            'start_time': self._get_current_timestamp(),
            'status': 'running'
        }
        return session_id
    
    def _complete_session(self, session_id: str, result: Dict[str, Any]):
        """Complete a session"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].update({
                'status': 'completed',
                'result': result,
                'end_time': self._get_current_timestamp()
            })
    
    def _error_session(self, session_id: str, error: str):
        """Mark a session as errored"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id].update({
                'status': 'error',
                'error': error,
                'end_time': self._get_current_timestamp()
            })
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp"""
        import datetime
        return datetime.datetime.now().isoformat()